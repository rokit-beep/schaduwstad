package com.nightforge.schaduwstad.network

import com.nightforge.schaduwstad.data.AckBody
import com.nightforge.schaduwstad.data.ChatBody
import com.nightforge.schaduwstad.data.ErrorBody
import com.nightforge.schaduwstad.data.GamesResponse
import com.nightforge.schaduwstad.data.HealthResponse
import com.nightforge.schaduwstad.data.NameBody
import com.nightforge.schaduwstad.data.ReadyBody
import com.nightforge.schaduwstad.data.Session
import com.nightforge.schaduwstad.data.SessionView
import com.nightforge.schaduwstad.data.TeamBody
import com.nightforge.schaduwstad.data.VoteBody
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

class GameApi(
    private val client: OkHttpClient,
    private val json: Json = Json { ignoreUnknownKeys = true },
) {
    private val media = "application/json".toMediaType()
    private val prefix = "/games/schaduwstad/api"

    suspend fun health(config: ConnectionConfig): HealthResponse = get(config, "/health", null)
    suspend fun games(config: ConnectionConfig): GamesResponse = get(config, "/platform/games", null)

    suspend fun createLobby(config: ConnectionConfig, name: String): SessionView =
        post(config, "$prefix/lobbies", json.encodeToString(NameBody(name)), null)

    suspend fun joinLobby(config: ConnectionConfig, code: String, name: String): SessionView =
        post(config, "$prefix/lobbies/${code.uppercase()}/join", json.encodeToString(NameBody(name)), null)

    suspend fun state(config: ConnectionConfig, session: Session): SessionView =
        get(config, "$prefix/lobbies/${session.lobbyCode}/state", session.token)

    suspend fun setTeam(config: ConnectionConfig, session: Session, team: String): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/team", json.encodeToString(TeamBody(team)), session.token)

    suspend fun setReady(config: ConnectionConfig, session: Session, ready: Boolean): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/ready", json.encodeToString(ReadyBody(ready)), session.token)

    suspend fun start(config: ConnectionConfig, session: Session): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/start", "", session.token)

    suspend fun vote(config: ConnectionConfig, session: Session, action: String): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/actions/vote", json.encodeToString(VoteBody(action)), session.token)

    suspend fun personal(config: ConnectionConfig, session: Session, action: String): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/actions/personal", json.encodeToString(VoteBody(action)), session.token)

    suspend fun followup(config: ConnectionConfig, session: Session, action: String): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/actions/followup", json.encodeToString(VoteBody(action)), session.token)

    suspend fun advance(config: ConnectionConfig, session: Session): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/actions/advance", "", session.token)

    suspend fun chat(config: ConnectionConfig, session: Session, body: String, share: String? = null): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/chat", json.encodeToString(ChatBody(body, share)), session.token)

    suspend fun ack(config: ConnectionConfig, session: Session, cinematics: List<String> = emptyList(), impacts: List<String> = emptyList()): SessionView =
        post(config, "$prefix/lobbies/${session.lobbyCode}/ack", json.encodeToString(AckBody(cinematics, impacts)), session.token)

    private suspend inline fun <reified T> get(config: ConnectionConfig, path: String, token: String?): T =
        execute(Request.Builder().url(config.httpBaseUrl() + path).apply { token?.let { header("Authorization", "Bearer $it") } }.get().build())

    private suspend inline fun <reified T> post(config: ConnectionConfig, path: String, body: String, token: String?): T =
        execute(
            Request.Builder().url(config.httpBaseUrl() + path).apply { token?.let { header("Authorization", "Bearer $it") } }
                .post(body.toRequestBody(media)).build(),
        )

    private suspend inline fun <reified T> execute(request: Request): T = withContext(Dispatchers.IO) {
        try {
            client.newCall(request).execute().use { response ->
                val body = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    val parsed = runCatching { json.decodeFromString<ErrorBody>(body).error }.getOrNull()
                    throw ApiException(parsed?.code ?: "error", parsed?.message ?: "Verzoek mislukt.", response.code)
                }
                runCatching { json.decodeFromString<T>(body) }
                    .getOrElse { throw ApiException("MALFORMED_RESPONSE", "Onverwacht serverantwoord.", response.code) }
            }
        } catch (error: ApiException) {
            throw error
        } catch (_: Exception) {
            throw ApiException("SERVER_UNREACHABLE", "Schaduwstad-server is niet bereikbaar.")
        }
    }
}
