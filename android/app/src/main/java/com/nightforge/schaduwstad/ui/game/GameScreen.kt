package com.nightforge.schaduwstad.ui.game

import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nightforge.schaduwstad.data.Action
import com.nightforge.schaduwstad.data.ChatMessage
import com.nightforge.schaduwstad.data.CinematicCue
import com.nightforge.schaduwstad.data.Clue
import com.nightforge.schaduwstad.data.SessionView
import com.nightforge.schaduwstad.ui.cinematic.CinematicId
import com.nightforge.schaduwstad.ui.cinematic.CinematicOverlay
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
    onPersonal: (String) -> Unit,
    onAdvance: () -> Unit,
    onLeave: () -> Unit,
    onToggleDossier: () -> Unit,
    onShareClue: (String) -> Unit,
    onReplay: (CinematicCue) -> Unit,
    onCinematicFinished: () -> Unit,
) {
    val view = state.view ?: return
    val accent = teamAccent(view.you?.team)
    val overlay = when {
        state.replayCue != null -> listOf(state.replayCue)
        state.cinematicQueue.isNotEmpty() -> state.cinematicQueue
        else -> emptyList()
    }
    Box(Modifier.fillMaxSize()) {
        CinematicBackdrop(dim = 0.78f) {
            Column(Modifier.fillMaxSize().imePadding().padding(horizontal = 16.dp, vertical = 12.dp)) {
                ConnectionPill(state.connected, reconnecting)
                Spacer(Modifier.height(8.dp))
                GameHeader(view, accent)
                Spacer(Modifier.height(8.dp))
                if (reconnecting) {
                    Text("Verbinding herstellen…", color = Amber, fontSize = 13.sp)
                    Spacer(Modifier.height(8.dp))
                }
                ErrorBanner(state.error)
                Column(
                    Modifier.weight(1f).verticalScroll(rememberScrollState()).animateContentSize(),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    when (view.phase) {
                        "briefing" -> BriefingPane(view.briefing, view.you?.team)
                        "huddle" -> HuddleHint()
                        "personal" -> PersonalPane(view, onPersonal)
                        "action" -> ActionPane(view, onVote)
                        "result" -> ResultPane(view, false, onReplay)
                        "eval" -> ResultPane(view, true, onReplay)
                    }
                    if (state.dossierOpen) {
                        if (view.you?.team == "detective") CaseDossier(view, onShareClue, onReplay)
                        else OpsDossierPane(view)
                    }
                }
                Spacer(Modifier.height(8.dp))
                TeamChat(state, accent, onDraft, onSend)
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) {
                        GhostButton(
                            if (view.you?.team == "mafia") "Operatie" else "Zaakdossier",
                            onToggleDossier,
                            Ice,
                        )
                    }
                    if (view.you?.isHost == true && view.phase != "eval") {
                        Box(Modifier.weight(1f)) {
                            GhostButton("Volgende fase", onAdvance, accent, !state.busy)
                        }
                    }
                }
                if (view.phase == "eval") {
                    Spacer(Modifier.height(8.dp))
                    GhostButton("Terug naar menu", onLeave, Fog)
                }
            }
        }
        if (overlay.isNotEmpty()) {
            CinematicOverlay(overlay, onFinished = onCinematicFinished)
        }
    }
}

@Composable
private fun GameHeader(view: SessionView, accent: Color) {
    Column(Modifier.fillMaxWidth()) {
        Text(
            "DAG ${view.day}",
            color = accent,
            letterSpacing = 3.sp,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
        )
        Text(
            "HAVENKADE 12",
            color = Fog,
            letterSpacing = 2.sp,
            fontSize = 11.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            phaseTitle(view.phase),
            color = Color.White,
            fontFamily = FontFamily.Serif,
            fontSize = 24.sp,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Spacer(Modifier.height(8.dp))
        ApRow(view.you?.ap ?: 0, view.you?.apMax ?: 2, accent)
    }
}

@Composable
private fun ApRow(ap: Int, max: Int, accent: Color) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text("ACTIEPUNTEN", color = Fog, letterSpacing = 2.sp, fontSize = 10.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.width(10.dp))
        repeat(max.coerceAtLeast(0).coerceAtMost(4)) { i ->
            Box(
                Modifier
                    .padding(end = 6.dp)
                    .size(12.dp)
                    .clip(CircleShape)
                    .background(if (i < ap) accent else Fog.copy(0.25f)),
            )
        }
        Text("$ap/$max", color = Color.White, fontSize = 12.sp)
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
        Text(
            "Spreek af in de teamchat. De andere kant hoort dit nooit. Daarna: persoonlijke acties, dan teamstrategie.",
            color = Fog,
            fontSize = 15.sp,
            lineHeight = 22.sp,
        )
    }
}

@Composable
private fun PersonalPane(view: SessionView, onPersonal: (String) -> Unit) {
    val ap = view.you?.ap ?: 0
    val taken = view.you?.personalActions ?: emptyList()
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("JOUW ACTIES  •  ${ap} AP", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        view.availableActions.forEach { action ->
            ActionCard(
                action = action,
                selected = action.id in taken,
                enabled = action.id !in taken && ap >= action.ap && action.id !in taken,
                badge = "${action.ap} AP",
                onClick = { onPersonal(action.id) },
            )
        }
    }
}

@Composable
private fun ActionPane(view: SessionView, onVote: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("TEAMSTRATEGIE", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        Text("Eén hoofdactie. Alleen jouw team ziet deze stemmen.", color = Fog, fontSize = 13.sp)
        view.availableActions.forEach { action ->
            val votes = view.voteTally.find { it.id == action.id }?.votes ?: 0
            ActionCard(
                action = action,
                selected = view.yourVote == action.id,
                enabled = true,
                badge = "$votes stemmen",
                onClick = { onVote(action.id) },
            )
        }
    }
}

@Composable
private fun ActionCard(action: Action, selected: Boolean, enabled: Boolean, badge: String, onClick: () -> Unit) {
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, if (selected) Amber else Fog.copy(0.3f), RoundedCornerShape(12.dp))
            .background(if (selected) Amber.copy(0.16f) else Ink.copy(0.4f))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(14.dp)
            .animateContentSize(),
    ) {
        Column {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(action.label.uppercase(), color = Color.White, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp, fontSize = 14.sp, modifier = Modifier.weight(1f))
                Text(badge, color = Amber, fontSize = 11.sp, letterSpacing = 1.sp)
            }
            if (!action.hint.isNullOrBlank()) Text(action.hint, color = Fog, fontSize = 13.sp)
        }
    }
}

@Composable
private fun ResultPane(view: SessionView, finale: Boolean, onReplay: (CinematicCue) -> Unit) {
    val result = view.result
    GlassCard(Modifier.fillMaxWidth(), Amber) {
        Text(if (finale) "DAG 1 VOLTOOID" else "RESULTAAT", color = Amber, letterSpacing = 3.sp, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text(result?.headline ?: "De nacht houdt haar mond.", color = Color.White, fontFamily = FontFamily.Serif, fontSize = 22.sp, lineHeight = 28.sp)
        Spacer(Modifier.height(10.dp))
        val beats = result?.beats.orEmpty()
        if (beats.isNotEmpty()) {
            beats.forEach { beat ->
                Text(beat.cause ?: "", color = Amber, fontSize = 12.sp, letterSpacing = 1.sp, fontWeight = FontWeight.Bold)
                Text(beat.effect ?: "", color = Fog, fontSize = 14.sp, lineHeight = 20.sp)
                Spacer(Modifier.height(8.dp))
            }
        } else {
            result?.events?.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
        }
        val debrief = if (view.you?.team == "mafia") result?.mafiaDebrief else result?.detectiveDebrief
        if (!debrief.isNullOrBlank()) {
            Text(debrief, color = Color(0xFFE8DFD2), fontSize = 15.sp, lineHeight = 22.sp)
            Spacer(Modifier.height(8.dp))
        }
        Spacer(Modifier.height(8.dp))
        Meter("EVIDENCE", (view.evidenceScore.coerceIn(0, 100)) / 100f, Ice)
        Spacer(Modifier.height(8.dp))
        Meter("HEAT", (view.heat.coerceIn(0, 100)) / 100f, PaperRed)
        Spacer(Modifier.height(10.dp))
        Text(
            "MAFFIA ${view.scores?.mafia ?: 0}    ·    DETECTIVES ${view.scores?.detective ?: 0}",
            color = Color.White,
            letterSpacing = 1.5.sp,
            fontSize = 13.sp,
        )
        val cue = result?.cinematics?.firstOrNull()
        if (cue != null) {
            Spacer(Modifier.height(10.dp))
            Text(
                "CINEMATIC OPNIEUW",
                color = Fog,
                fontSize = 11.sp,
                letterSpacing = 2.sp,
                modifier = Modifier.clickable { onReplay(cue) },
            )
        }
        if (finale) {
            Spacer(Modifier.height(16.dp))
            Text("DE STAD SLAAPT NOOIT.", color = PaperRed, letterSpacing = 3.sp, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Text("VOLGENDE ZAAK — BINNENKORT", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        }
    }
}

@Composable
private fun CaseDossier(view: SessionView, onShare: (String) -> Unit, onReplay: (CinematicCue) -> Unit) {
    GlassCard(Modifier.fillMaxWidth(), Ice) {
        SectionTitle("ZAAKDOSSIER", Ice)
        if (view.clues.isEmpty()) {
            Text("Nog geen clues. Onderzoek de kade.", color = Fog, fontSize = 14.sp)
        } else {
            view.clues.forEach { clue ->
                ClueCard(clue, onShare, onReplay)
                Spacer(Modifier.height(10.dp))
            }
        }
    }
}

@Composable
private fun ClueCard(clue: Clue, onShare: (String) -> Unit, onReplay: (CinematicCue) -> Unit) {
    val ctx = LocalContext.current
    val thumb = CinematicId.fromWire(clue.cinematic)?.thumbRes(ctx) ?: 0
    Column(Modifier.fillMaxWidth().border(1.dp, Ice.copy(0.25f), RoundedCornerShape(12.dp)).padding(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            if (thumb != 0) {
                Image(
                    painterResource(thumb),
                    contentDescription = clue.name,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(64.dp).clip(RoundedCornerShape(8.dp)),
                )
            }
            Column(Modifier.weight(1f)) {
                Text(clue.name.uppercase(), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text(statusLabel(clue.status), color = Ice, fontSize = 11.sp, letterSpacing = 1.5.sp)
            }
        }
        Spacer(Modifier.height(8.dp))
        Text(clue.description, color = Fog, fontSize = 13.sp, lineHeight = 18.sp)
        Text("Gevonden tijdens  •  ${clue.foundDuring ?: "—"}", color = Fog.copy(0.8f), fontSize = 11.sp)
        Text("Betrouwbaarheid  ${clue.reliability}%", color = Amber, fontSize = 11.sp)
        Spacer(Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("DELEN", color = Ice, fontSize = 11.sp, letterSpacing = 2.sp, modifier = Modifier.clickable { onShare(clue.id) })
            if (!clue.cinematic.isNullOrBlank()) {
                Text(
                    "CINEMATIC OPNIEUW",
                    color = Fog,
                    fontSize = 11.sp,
                    letterSpacing = 1.5.sp,
                    modifier = Modifier.clickable {
                        onReplay(CinematicCue(id = clue.cinematic, title = clue.name, kind = "clue"))
                    },
                )
            }
        }
    }
}

@Composable
private fun OpsDossierPane(view: SessionView) {
    val ops = view.opsDossier
    GlassCard(Modifier.fillMaxWidth(), PaperRed) {
        SectionTitle("OPERATIEDOSSIER", PaperRed)
        if (ops == null) {
            Text("Nog geen operatiegegevens.", color = Fog, fontSize = 14.sp)
            return@GlassCard
        }
        Text("RISICO'S", color = Amber, fontSize = 11.sp, letterSpacing = 2.sp)
        ops.risks.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
        Spacer(Modifier.height(8.dp))
        Text("BESCHERMD", color = Amber, fontSize = 11.sp, letterSpacing = 2.sp)
        ops.protected.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
        Spacer(Modifier.height(8.dp))
        Text("DREIGING", color = Amber, fontSize = 11.sp, letterSpacing = 2.sp)
        ops.threats.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
    }
}

@Composable
private fun Meter(label: String, value: Float, color: Color) {
    Column(Modifier.fillMaxWidth()) {
        Text(label, color = color, letterSpacing = 2.sp, fontSize = 10.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { value.coerceIn(0f, 1f) },
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
    Column(
        Modifier
            .fillMaxWidth()
            .height(200.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(Color(0xCC0B0A0C))
            .padding(10.dp),
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(
                "TEAMCHAT  •  ${if (state.view?.you?.team == "mafia") "MAFFIA" else "DETECTIVES"}",
                color = accent,
                letterSpacing = 2.sp,
                fontSize = 10.sp,
            )
            if (chat.isNotEmpty() && list.canScrollForward) {
                Text("NIEUW", color = Amber, fontSize = 10.sp, letterSpacing = 1.sp)
            }
        }
        Spacer(Modifier.height(6.dp))
        if (chat.isEmpty()) {
            Text("Nog geen berichten. Alleen jouw team hoort dit.", color = Fog.copy(0.7f), fontSize = 13.sp, modifier = Modifier.weight(1f))
        } else {
            LazyColumn(state = list, modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(chat, key = { it.id ?: it.body + it.at }) { ChatBubble(it, accent, it.senderId == state.view?.you?.id) }
            }
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
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(message.senderName + if (mine) "  ·  jij" else "", color = Fog, fontSize = 11.sp)
                val clock = message.at?.substringAfter("T")?.take(5)
                if (!clock.isNullOrBlank()) Text(clock, color = Fog.copy(0.6f), fontSize = 10.sp)
            }
            Text(message.body, color = Color.White, fontSize = 14.sp)
            message.share?.label?.let { label ->
                Spacer(Modifier.height(4.dp))
                Box(Modifier.clip(RoundedCornerShape(8.dp)).background(accent.copy(0.18f)).padding(8.dp)) {
                    Text(label, color = accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

private fun phaseTitle(phase: String) = when (phase) {
    "briefing" -> "Briefing"
    "huddle" -> "Teamoverleg"
    "personal" -> "Individuele acties"
    "action" -> "Teamstrategie"
    "result" -> "De kade antwoordt"
    "eval" -> "De stad slaapt nooit"
    else -> phase
}

private fun statusLabel(status: String) = when (status) {
    "discovered" -> "ONTDEKT"
    "verified" -> "GEVERIFIEERD"
    "disputed" -> "BETWIJFELD"
    else -> "ONBEKEND"
}
