package com.nightforge.schaduwstad.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class HealthResponse(
    val status: String? = null,
    val service: String? = null,
    val version: String? = null,
    val port: Int? = null,
)

@Serializable
data class GamesResponse(val games: List<GameInfo> = emptyList())

@Serializable
data class GameInfo(val id: String, val name: String, val version: String? = null, val status: String? = null)

@Serializable
data class ErrorBody(val error: ErrorDetail? = null)

@Serializable
data class ErrorDetail(val code: String? = null, val message: String? = null)

@Serializable
data class NameBody(@SerialName("player_name") val playerName: String)

@Serializable
data class TeamBody(val team: String)

@Serializable
data class ReadyBody(val ready: Boolean)

@Serializable
data class VoteBody(val action: String)

@Serializable
data class ChatBody(val body: String = "", val share: String? = null)

@Serializable
data class SessionView(
    @SerialName("session_token") val sessionToken: String? = null,
    val lobbyCode: String = "",
    val status: String = "waiting",
    val day: Int = 1,
    val phase: String = "briefing",
    val caseId: String? = null,
    val you: You? = null,
    val players: List<Player> = emptyList(),
    val teamSize: TeamSize? = null,
    val chat: List<ChatMessage> = emptyList(),
    val briefing: String? = null,
    val availableActions: List<Action> = emptyList(),
    val yourVote: String? = null,
    val voteTally: List<VoteTally> = emptyList(),
    val scores: Scores? = null,
    val heat: Int = 0,
    val evidence: String? = null,
    val evidenceScore: Int = 0,
    val clues: List<Clue> = emptyList(),
    val opsDossier: OpsDossier? = null,
    val result: DayResult? = null,
    val canStart: Boolean = false,
)

@Serializable
data class You(
    val id: String,
    val name: String,
    val team: String? = null,
    val ready: Boolean = false,
    val isHost: Boolean = false,
    val ap: Int = 2,
    val apMax: Int = 2,
    val personalActions: List<String> = emptyList(),
)

@Serializable
data class Player(
    val id: String,
    val name: String,
    val team: String? = null,
    val ready: Boolean = false,
    val isYou: Boolean = false,
    val isHost: Boolean = false,
)

@Serializable
data class TeamSize(val mafia: Int = 0, val detective: Int = 0, val cap: Int = 6)

@Serializable
data class ChatMessage(
    val id: String? = null,
    val team: String? = null,
    val senderId: String? = null,
    val senderName: String = "",
    val body: String = "",
    val at: String? = null,
    val share: ChatShare? = null,
)

@Serializable
data class ChatShare(
    val kind: String? = null,
    val clueId: String? = null,
    val label: String? = null,
    val status: String? = null,
)

@Serializable
data class Action(val id: String, val label: String, val hint: String? = null, val ap: Int = 1, val cinematic: String? = null)

@Serializable
data class VoteTally(val id: String, val label: String, val votes: Int = 0)

@Serializable
data class Scores(val mafia: Int = 0, val detective: Int = 0)

@Serializable
data class Clue(
    val id: String,
    val name: String = "",
    val description: String = "",
    val status: String = "unknown",
    val foundDuring: String? = null,
    val reliability: Int = 0,
    val cinematic: String? = null,
    val related: List<String> = emptyList(),
)

@Serializable
data class OpsDossier(
    val heat: Int = 0,
    val evidenceThreat: Int = 0,
    val protected: List<String> = emptyList(),
    val threats: List<String> = emptyList(),
    val risks: List<String> = emptyList(),
)

@Serializable
data class CinematicCue(
    val id: String,
    val title: String? = null,
    val kind: String? = null,
    val team: String? = null,
    val replayable: Boolean = true,
)

@Serializable
data class Beat(
    val id: String? = null,
    val cause: String? = null,
    val effect: String? = null,
    val cinematic: String? = null,
    val team: String? = null,
    val evidenceDelta: Int = 0,
    val heatDelta: Int = 0,
)

@Serializable
data class DayResult(
    val mafiaAction: String? = null,
    val detectiveAction: String? = null,
    val mafiaPersonal: List<String> = emptyList(),
    val detectivePersonal: List<String> = emptyList(),
    val mafiaDelta: Int = 0,
    val detectiveDelta: Int = 0,
    val heat: Int = 0,
    val evidence: String? = null,
    val evidenceScore: Int = 0,
    val headline: String? = null,
    val mafiaDebrief: String? = null,
    val detectiveDebrief: String? = null,
    val events: List<String> = emptyList(),
    val beats: List<Beat> = emptyList(),
    val cinematics: List<CinematicCue> = emptyList(),
    val clues: Map<String, Clue> = emptyMap(),
    val contested: List<String> = emptyList(),
)

@Serializable
data class SocketEnvelope(val type: String, val view: SessionView? = null)

data class Session(val token: String, val lobbyCode: String)
