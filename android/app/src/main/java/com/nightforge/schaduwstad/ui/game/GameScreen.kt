package com.nightforge.schaduwstad.ui.game

import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nightforge.schaduwstad.data.ChatMessage
import com.nightforge.schaduwstad.ui.components.CinematicBackdrop
import com.nightforge.schaduwstad.ui.components.ConnectionPill
import com.nightforge.schaduwstad.ui.components.ErrorBanner
import com.nightforge.schaduwstad.ui.components.GhostButton
import com.nightforge.schaduwstad.ui.components.GlassCard
import com.nightforge.schaduwstad.ui.components.SectionTitle
import com.nightforge.schaduwstad.ui.theme.Amber
import com.nightforge.schaduwstad.ui.theme.Fog
import com.nightforge.schaduwstad.ui.theme.Ice
import com.nightforge.schaduwstad.ui.theme.Ink
import com.nightforge.schaduwstad.ui.theme.PaperRed
import com.nightforge.schaduwstad.ui.theme.teamAccent
import com.nightforge.schaduwstad.viewmodel.UiState

@Composable
fun GameScreen(
    state: UiState,
    reconnecting: Boolean,
    onDraft: (String) -> Unit,
    onSend: () -> Unit,
    onVote: (String) -> Unit,
    onAdvance: () -> Unit,
    onLeave: () -> Unit,
) {
    val view = state.view ?: return
    val accent = teamAccent(view.you?.team)
    val phase = view.phase
    CinematicBackdrop(dim = 0.78f) {
        Column(Modifier.fillMaxSize().imePadding().padding(16.dp)) {
            ConnectionPill(state.connected, reconnecting)
            Spacer(Modifier.height(8.dp))
            Text("DAG ${view.day}  •  HAVENKADE 12", color = accent, letterSpacing = 3.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Text(phaseTitle(phase), color = Color.White, fontFamily = FontFamily.Serif, fontSize = 26.sp)
            Spacer(Modifier.height(8.dp))
            if (reconnecting) {
                Text("Verbinding herstellen…", color = Amber, fontSize = 13.sp)
                Spacer(Modifier.height(8.dp))
            }
            ErrorBanner(state.error)
            when (phase) {
                "briefing" -> BriefingPane(view.briefing, view.you?.team)
                "huddle" -> HuddleHint()
                "action" -> ActionPane(view, onVote)
                "result" -> ResultPane(view, false)
                "eval" -> ResultPane(view, true)
            }
            Spacer(Modifier.height(10.dp))
            TeamChat(state, accent, onDraft, onSend)
            Spacer(Modifier.height(8.dp))
            if (view.you?.isHost == true && phase != "eval") {
                GhostButton("Volgende fase", onAdvance, accent, !state.busy)
                Spacer(Modifier.height(8.dp))
            }
            if (phase == "eval") {
                GhostButton("Terug naar menu", onLeave, Fog)
            }
        }
    }
}

@Composable
private fun BriefingPane(text: String?, team: String?) {
    GlassCard(Modifier.fillMaxWidth(), teamAccent(team)) {
        SectionTitle(if (team == "mafia") "PRIVÉ — MAFFIA" else "DOSSIER — RECHERCHE", teamAccent(team))
        Text(text ?: "Wachten op briefing…", color = Color(0xFFEDE6DA), fontSize = 16.sp, lineHeight = 24.sp)
    }
}

@Composable
private fun HuddleHint() {
    GlassCard(Modifier.fillMaxWidth(), Amber) {
        Text("TEAMOVERLEG", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text("Spreek af in de teamchat. De andere kant hoort dit nooit. Als jullie klaar zijn schuift de host door naar de actie.", color = Fog, fontSize = 15.sp, lineHeight = 22.sp)
    }
}

@Composable
private fun ActionPane(view: com.nightforge.schaduwstad.data.SessionView, onVote: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("STEM OP EEN ACTIE", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        view.availableActions.forEach { action ->
            val selected = view.yourVote == action.id
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .border(1.dp, if (selected) Amber else Fog.copy(0.3f), RoundedCornerShape(12.dp))
                    .background(if (selected) Amber.copy(0.16f) else Ink.copy(0.4f))
                    .clickable { onVote(action.id) }
                    .padding(14.dp)
                    .animateContentSize(),
            ) {
                Column {
                    Text(action.label.uppercase(), color = Color.White, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp, fontSize = 14.sp)
                    if (!action.hint.isNullOrBlank()) Text(action.hint, color = Fog, fontSize = 13.sp)
                }
            }
        }
    }
}

@Composable
private fun ResultPane(view: com.nightforge.schaduwstad.data.SessionView, finale: Boolean) {
    val result = view.result
    GlassCard(Modifier.fillMaxWidth(), Amber) {
        Text(if (finale) "DAG 1 VOLTOOID" else "RESULTAAT", color = Amber, letterSpacing = 3.sp, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text(result?.headline ?: "De nacht houdt haar mond.", color = Color.White, fontFamily = FontFamily.Serif, fontSize = 22.sp, lineHeight = 28.sp)
        Spacer(Modifier.height(10.dp))
        result?.events?.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
        val debrief = if (view.you?.team == "mafia") result?.mafiaDebrief else result?.detectiveDebrief
        if (!debrief.isNullOrBlank()) {
            Spacer(Modifier.height(8.dp))
            Text(debrief, color = Color(0xFFE8DFD2), fontSize = 15.sp, lineHeight = 22.sp)
        }
        Spacer(Modifier.height(14.dp))
        Meter("EVIDENCE", evidenceLevel(view.evidence), Ice)
        Spacer(Modifier.height(8.dp))
        Meter("HEAT", (view.heat.coerceIn(0, 100)) / 100f, PaperRed)
        Spacer(Modifier.height(10.dp))
        Text("MAFFIA ${view.scores?.mafia ?: 0}    ·    DETECTIVES ${view.scores?.detective ?: 0}", color = Color.White, letterSpacing = 1.5.sp, fontSize = 13.sp)
        val lead = when {
            (view.scores?.mafia ?: 0) > (view.scores?.detective ?: 0) -> "Maffia heeft voorlopig voordeel."
            (view.scores?.detective ?: 0) > (view.scores?.mafia ?: 0) -> "Recherche heeft voorlopig voordeel."
            else -> "De stad houdt het spannend."
        }
        Text(lead, color = Fog, fontSize = 13.sp)
        if (finale) {
            Spacer(Modifier.height(16.dp))
            Text("DE STAD SLAAPT NOOIT.", color = PaperRed, letterSpacing = 3.sp, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Text("VOLGENDE ZAAK — BINNENKORT", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        }
    }
}

@Composable
private fun Meter(label: String, value: Float, color: Color) {
    Column {
        Text(label, color = color, letterSpacing = 2.sp, fontSize = 10.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { value },
            modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(99.dp)),
            color = color,
            trackColor = Color.White.copy(0.08f),
        )
    }
}

@Composable
private fun TeamChat(state: UiState, accent: Color, onDraft: (String) -> Unit, onSend: () -> Unit) {
    val list = rememberLazyListState()
    val chat = state.view?.chat ?: emptyList()
    LaunchedEffect(chat.size) { if (chat.isNotEmpty()) list.animateScrollToItem(chat.lastIndex) }
    Column(Modifier.fillMaxWidth().height(220.dp).clip(RoundedCornerShape(14.dp)).background(Color(0xCC0B0A0C)).padding(10.dp)) {
        Text("TEAMCHAT  •  ${if (state.view?.you?.team == "mafia") "MAFFIA" else "DETECTIVES"}", color = accent, letterSpacing = 2.sp, fontSize = 10.sp)
        Spacer(Modifier.height(6.dp))
        LazyColumn(state = list, modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(chat, key = { it.id ?: it.body + it.at }) { ChatBubble(it, accent, it.senderId == state.view?.you?.id) }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextField(
                value = state.chatDraft,
                onValueChange = onDraft,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Alleen jouw team hoort dit…", color = Fog.copy(0.7f), fontSize = 13.sp) },
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Color.Transparent,
                    unfocusedContainerColor = Color.Transparent,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    cursorColor = accent,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                ),
                singleLine = true,
            )
            Text("STUUR", color = accent, fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp, fontSize = 12.sp, modifier = Modifier.padding(8.dp).clickable(onClick = onSend))
        }
    }
}

@Composable
private fun ChatBubble(message: ChatMessage, accent: Color, mine: Boolean) {
    Row(verticalAlignment = Alignment.Top) {
        Box(Modifier.width(28.dp).height(28.dp).clip(CircleShape).background(accent.copy(0.3f)), contentAlignment = Alignment.Center) {
            Text(message.senderName.take(1).uppercase(), color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
        Spacer(Modifier.width(8.dp))
        Column {
            Text(message.senderName + if (mine) "  ·  jij" else "", color = Fog, fontSize = 11.sp)
            Text(message.body, color = Color.White, fontSize = 14.sp)
        }
    }
}

private fun phaseTitle(phase: String) = when (phase) {
    "briefing" -> "Cinematische briefing"
    "huddle" -> "Teamoverleg"
    "action" -> "Actiekeuze"
    "result" -> "De kade antwoordt"
    "eval" -> "De stad slaapt nooit"
    else -> phase
}

private fun evidenceLevel(value: String?): Float = when (value) {
    "hidden" -> 0.12f
    "partial" -> 0.55f
    "open" -> 0.92f
    else -> 0.08f
}
