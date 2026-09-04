package com.nightforge.schaduwstad.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nightforge.schaduwstad.data.CinematicCue
import com.nightforge.schaduwstad.data.Session
import com.nightforge.schaduwstad.data.SessionView
import com.nightforge.schaduwstad.data.SettingsStore
import com.nightforge.schaduwstad.network.ApiException
import com.nightforge.schaduwstad.network.ConnectionConfig
import com.nightforge.schaduwstad.network.GameApi
import com.nightforge.schaduwstad.network.GameSocket
import com.nightforge.schaduwstad.network.SocketStatus
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

enum class Dest { Intro, Menu, How, Settings, Name, Join, Lobby, Game }

data class UiState(
    val dest: Dest = Dest.Intro,
    val host: String = ConnectionConfig.DEFAULT_HOST,
    val port: Int = ConnectionConfig.DEFAULT_PORT,
    val playerName: String = "",
    val joinCode: String = "",
    val chatDraft: String = "",
    val connected: Boolean = false,
    val reconnecting: Boolean = false,
    val error: String? = null,
    val notice: String? = null,
    val session: Session? = null,
    val view: SessionView? = null,
    val busy: Boolean = false,
    val cinematicQueue: List<CinematicCue> = emptyList(),
    val dossierOpen: Boolean = false,
    val replayCue: CinematicCue? = null,
)

class GameViewModel(app: Application) : AndroidViewModel(app) {
    private val settings = SettingsStore(app)
    private val client = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()
    private val api = GameApi(client)
    private val socket = GameSocket(client, viewModelScope)
    private val _ui = MutableStateFlow(UiState(dest = if (introConsumed) Dest.Menu else Dest.Intro))
    val ui: StateFlow<UiState> = _ui
    val socketStatus: StateFlow<SocketStatus> = socket.status
    private var pollJob: Job? = null
    private var playedResultKey: String? = null

    init {
        viewModelScope.launch {
            combine(settings.host, settings.port, settings.playerName) { h, p, n -> Triple(h, p, n) }
                .collect { (h, p, n) ->
                    _ui.update { it.copy(host = h, port = p, playerName = n) }
                    ping()
                }
        }
        viewModelScope.launch {
            socket.events.collect { envelope ->
                envelope.view?.let { applyView(it) }
            }
        }
        viewModelScope.launch {
            socket.status.collect { status ->
                _ui.update {
                    it.copy(
                        reconnecting = status == SocketStatus.RECONNECTING,
                        connected = it.connected || status == SocketStatus.CONNECTED,
                    )
                }
            }
        }
    }

    fun consumeIntro() {
        introConsumed = true
        _ui.update { it.copy(dest = if (it.playerName.length >= 2) Dest.Menu else Dest.Name) }
    }

    fun replayIntro() {
        introConsumed = false
        _ui.update { it.copy(dest = Dest.Intro) }
    }

    fun go(dest: Dest) { _ui.update { it.copy(dest = dest, error = null) } }
    fun setJoinCode(value: String) { _ui.update { it.copy(joinCode = value.filter { ch -> ch.isLetterOrDigit() }.take(4).uppercase()) } }
    fun setChatDraft(value: String) { _ui.update { it.copy(chatDraft = value.take(240)) } }
    fun clearError() { _ui.update { it.copy(error = null, notice = null) } }
    fun toggleDossier() { _ui.update { it.copy(dossierOpen = !it.dossierOpen) } }
    fun closeDossier() { _ui.update { it.copy(dossierOpen = false) } }

    fun cinematicFinished() {
        _ui.update { it.copy(cinematicQueue = emptyList(), replayCue = null) }
    }

    fun replayCinematic(cue: CinematicCue) {
        _ui.update { it.copy(replayCue = cue, cinematicQueue = emptyList()) }
    }

    fun saveName(name: String) {
        viewModelScope.launch {
            settings.setPlayerName(name)
            _ui.update { it.copy(playerName = name.trim(), dest = Dest.Menu) }
        }
    }

    fun saveServer(host: String, port: Int) {
        viewModelScope.launch {
            settings.setHost(host)
            settings.setPort(port)
            ping()
        }
    }

    fun ping() {
        val cfg = config()
        if (!cfg.isUsable()) {
            _ui.update { it.copy(connected = false) }
            return
        }
        viewModelScope.launch {
            runCatching {
                val health = api.health(cfg)
                val games = api.games(cfg)
                health.status == "ok" && games.games.any { it.id == "schaduwstad" }
            }.onSuccess { ok -> _ui.update { it.copy(connected = ok, error = if (ok) null else "Schaduwstad niet gevonden op deze server.") } }
                .onFailure { _ui.update { it.copy(connected = false) } }
        }
    }

    fun createLobby() = mutate { cfg, name ->
        val view = api.createLobby(cfg, name)
        attach(view)
        Dest.Lobby
    }

    fun joinLobby() = mutate { cfg, name ->
        val code = _ui.value.joinCode
        if (code.length < 4) throw ApiException("bad_code", "Voer een lobbycode van 4 tekens in.")
        val view = api.joinLobby(cfg, code, name)
        attach(view)
        Dest.Lobby
    }

    fun chooseTeam(team: String) = mutate { cfg, _ ->
        applyView(api.setTeam(cfg, requireSession(), team)); null
    }

    fun toggleReady() = mutate { cfg, _ ->
        val ready = !(_ui.value.view?.you?.ready ?: false)
        applyView(api.setReady(cfg, requireSession(), ready)); null
    }

    fun startGame() = mutate { cfg, _ ->
        applyView(api.start(cfg, requireSession()))
        Dest.Game
    }

    fun vote(action: String) = mutate { cfg, _ ->
        applyView(api.vote(cfg, requireSession(), action)); null
    }

    fun personal(action: String) = mutate { cfg, _ ->
        applyView(api.personal(cfg, requireSession(), action)); null
    }

    fun advance() = mutate { cfg, _ ->
        applyView(api.advance(cfg, requireSession())); null
    }

    fun sendChat() {
        val body = _ui.value.chatDraft.trim()
        if (body.isEmpty()) return
        val session = _ui.value.session ?: return
        _ui.update { it.copy(chatDraft = "") }
        if (!socket.sendChat(body)) {
            mutate { cfg, _ -> applyView(api.chat(cfg, session, body)); null }
        }
    }

    fun shareClue(clueId: String) {
        val session = _ui.value.session ?: return
        mutate { cfg, _ -> applyView(api.chat(cfg, session, "", clueId)); null }
    }

    fun leaveToMenu() {
        pollJob?.cancel()
        socket.close()
        playedResultKey = null
        _ui.update { it.copy(dest = Dest.Menu, session = null, view = null, error = null, cinematicQueue = emptyList(), dossierOpen = false) }
    }

    private fun attach(view: SessionView) {
        val token = view.sessionToken ?: return
        val session = Session(token, view.lobbyCode)
        applyView(view.copy(sessionToken = token))
        _ui.update { it.copy(session = session) }
        socket.connect(config(), session)
        startPolling()
    }

    private fun applyView(view: SessionView) {
        val dest = when {
            view.status == "started" -> Dest.Game
            view.status == "waiting" && _ui.value.session != null -> Dest.Lobby
            else -> _ui.value.dest
        }
        val key = "${view.day}:${view.phase}:${view.result?.headline}"
        val queue = if (view.phase == "result" && key != playedResultKey && view.result?.cinematics?.isNotEmpty() == true) {
            playedResultKey = key
            view.result.cinematics
        } else {
            _ui.value.cinematicQueue
        }
        _ui.update { it.copy(view = view, dest = dest, error = null, cinematicQueue = queue) }
    }

    private fun startPolling() {
        pollJob?.cancel()
        pollJob = viewModelScope.launch {
            while (true) {
                delay(if (socket.status.value == SocketStatus.CONNECTED) 4000 else 1500)
                val session = _ui.value.session ?: continue
                runCatching { applyView(api.state(config(), session)) }
            }
        }
    }

    private fun mutate(block: suspend (ConnectionConfig, String) -> Dest?) {
        val name = _ui.value.playerName.trim()
        if (name.length < 2) {
            _ui.update { it.copy(dest = Dest.Name, error = "Kies eerst een spelersnaam.") }
            return
        }
        viewModelScope.launch {
            _ui.update { it.copy(busy = true, error = null) }
            runCatching { block(config(), name) }
                .onSuccess { dest -> _ui.update { it.copy(busy = false, dest = dest ?: it.dest) } }
                .onFailure { err ->
                    val message = (err as? ApiException)?.message ?: "Er ging iets mis."
                    _ui.update { it.copy(busy = false, error = message) }
                }
        }
    }

    private fun requireSession(): Session = _ui.value.session ?: throw ApiException("no_session", "Geen actieve sessie.")
    private fun config() = ConnectionConfig(_ui.value.host, _ui.value.port)

    override fun onCleared() {
        pollJob?.cancel()
        socket.close()
        super.onCleared()
    }

    companion object {
        @Volatile var introConsumed: Boolean = false
    }
}
