package com.nightforge.schaduwstad.network

import com.nightforge.schaduwstad.data.Session
import com.nightforge.schaduwstad.data.SocketEnvelope
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.atomic.AtomicBoolean

enum class SocketStatus { DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, ERROR }

class GameSocket(
    private val client: OkHttpClient,
    private val scope: CoroutineScope,
    private val json: Json = Json { ignoreUnknownKeys = true },
) {
    private val _status = MutableStateFlow(SocketStatus.DISCONNECTED)
    val status: StateFlow<SocketStatus> = _status
    private val _events = MutableSharedFlow<SocketEnvelope>(extraBufferCapacity = 32)
    val events: SharedFlow<SocketEnvelope> = _events
    private var socket: WebSocket? = null
    private var reconnectJob: Job? = null
    private var active: Pair<ConnectionConfig, Session>? = null
    private val intentionalClose = AtomicBoolean(false)

    fun connect(config: ConnectionConfig, session: Session) {
        if (active == config to session && socket != null) return
        close()
        intentionalClose.set(false)
        active = config to session
        open(config, session)
    }

    private fun open(config: ConnectionConfig, session: Session) {
        socket?.cancel()
        socket = null
        _status.value = if (_status.value == SocketStatus.RECONNECTING) SocketStatus.RECONNECTING else SocketStatus.CONNECTING
        val request = Request.Builder().url(config.webSocketUrl(session.lobbyCode, session.token)).build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _status.value = SocketStatus.CONNECTED
                webSocket.send("""{"type":"sync"}""")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                runCatching { json.decodeFromString<SocketEnvelope>(text) }
                    .onSuccess { _events.tryEmit(it) }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                socket = null
                if (!intentionalClose.get()) scheduleReconnect(config, session)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                socket = null
                if (!intentionalClose.get()) scheduleReconnect(config, session) else _status.value = SocketStatus.DISCONNECTED
            }
        })
    }

    fun sendChat(body: String): Boolean {
        val payload = buildJsonObject {
            put("type", "chat")
            put("body", body)
        }
        return socket?.send(payload.toString()) == true
    }

    private fun scheduleReconnect(config: ConnectionConfig, session: Session) {
        if (reconnectJob?.isActive == true || intentionalClose.get()) return
        reconnectJob = scope.launch {
            for (delayMillis in reconnectDelays) {
                if (intentionalClose.get() || active != config to session) return@launch
                _status.value = SocketStatus.RECONNECTING
                delay(delayMillis)
                if (intentionalClose.get()) return@launch
                open(config, session)
                delay(1_200)
                if (_status.value == SocketStatus.CONNECTED) return@launch
            }
            _status.value = SocketStatus.ERROR
        }
    }

    fun close() {
        intentionalClose.set(true)
        reconnectJob?.cancel()
        reconnectJob = null
        active = null
        socket?.close(1000, "Client closing")
        socket = null
        _status.value = SocketStatus.DISCONNECTED
    }

    companion object {
        val reconnectDelays = listOf(1_000L, 2_000L, 4_000L, 8_000L)
    }
}
