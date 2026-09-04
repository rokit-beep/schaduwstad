package com.nightforge.schaduwstad.ui.game

import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
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
import androidx.compose.foundation.layout.heightIn
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
import androidx.compose.runtime.getValue
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
import com.nightforge.schaduwstad.data.FollowUp
import com.nightforge.schaduwstad.data.Impact
import com.nightforge.schaduwstad.data.SessionView
import com.nightforge.schaduwstad.ui.cinematic.CinematicCatalog
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
    onLock: () -> Unit,
    onUnlock: () -> Unit,
    onAdvance: () -> Unit,
    onLeave: () -> Unit,
    onToggleDossier: () -> Unit,
    onToggleInbox: () -> Unit,
    onShareClue: (String) -> Unit,
    onReplay: (CinematicCue) -> Unit,
    onCinematicFinished: () -> Unit,
    onImpactAck: () -> Unit,
    onFollowUp: (String) -> Unit,
    onDismissConsequence: () -> Unit,
) {
    val view = state.view ?: return
    val accent = teamAccent(view.you?.team)
    val overlay = when {
        state.replayCue != null -> listOf(state.replayCue)
        state.cinematicQueue.isNotEmpty() -> state.cinematicQueue
        else -> emptyList()
    }
    val playing = overlay.isNotEmpty()
    val showImpacts = !playing && !state.showConsequence && state.impactQueue.isNotEmpty()
    val playable = view.phase in setOf("play", "briefing", "huddle", "personal", "action")
    Box(Modifier.fillMaxSize()) {
        CinematicBackdrop(dim = 0.78f) {
            Column(Modifier.fillMaxSize().imePadding().padding(horizontal = 16.dp, vertical = 10.dp)) {
                ConnectionPill(state.connected, reconnecting)
                Spacer(Modifier.height(6.dp))
                GameHeader(view, accent)
                Spacer(Modifier.height(6.dp))
                if (reconnecting) {
                    Text("Verbinding herstellen…", color = Amber, fontSize = 13.sp)
                    Spacer(Modifier.height(6.dp))
                }
                ErrorBanner(state.error)
                Column(
                    Modifier.weight(1f).verticalScroll(rememberScrollState()).animateContentSize(),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    when {
                        playable -> PlayPane(view, onPersonal, onVote, onLock, onUnlock)
                        view.phase == "result" -> ResultPane(view, false, onReplay)
                        view.phase == "eval" -> ResultPane(view, true, onReplay)
                    }
                    if (state.inboxOpen) InboxPane(view)
                    if (state.dossierOpen) {
                        if (view.you?.team == "detective") CaseDossier(view, onShareClue, onReplay)
                        else OpsDossierPane(view)
                    }
                    Spacer(Modifier.height(8.dp))
                }
                Spacer(Modifier.height(6.dp))
                TeamChat(state, accent, onDraft, onSend)
                Spacer(Modifier.height(6.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) {
                        GhostButton(
                            if (view.you?.team == "mafia") "Operatie" else "Zaakdossier",
                            onToggleDossier,
                            Ice,
                        )
                    }
                    Box(Modifier.weight(1f)) {
                        GhostButton("Ontwikkelingen", onToggleInbox, Amber)
                    }
                }
                if (view.you?.isHost == true && view.phase != "eval") {
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "DEV: FASE FORCEREN",
                        color = Fog.copy(0.7f),
                        letterSpacing = 2.sp,
                        fontSize = 10.sp,
                        modifier = Modifier
                            .align(Alignment.CenterHorizontally)
                            .clickable(enabled = !state.busy, onClick = onAdvance)
                            .padding(6.dp),
                    )
                }
                if (view.phase == "eval") {
                    Spacer(Modifier.height(8.dp))
                    GhostButton("Terug naar menu", onLeave, Fog)
                }
            }
        }
        if (overlay.isNotEmpty()) {
            CinematicOverlay(overlay, onFinished = onCinematicFinished)
        } else if (state.showConsequence && view.result != null) {
            ConsequenceOverlay(view, onFollowUp, onDismissConsequence, state.busy)
        } else if (showImpacts) {
            ImpactOverlay(state.impactQueue, onImpactAck)
        }
    }
}

@Composable
private fun GameHeader(view: SessionView, accent: Color) {
    Column(Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("DAG ${view.day}", color = accent, letterSpacing = 3.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            val left = view.roundSecondsLeft
            if (left != null) {
                val mm = left / 60
                val ss = left % 60
                Text("NOG %d:%02d".format(mm, ss), color = Fog, letterSpacing = 2.sp, fontSize = 11.sp)
            }
        }
        Text(
            view.caseTitle ?: "HAVENKADE 12",
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
            fontSize = 22.sp,
            lineHeight = 26.sp,
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
private fun PlayPane(
    view: SessionView,
    onPersonal: (String) -> Unit,
    onVote: (String) -> Unit,
    onLock: () -> Unit,
    onUnlock: () -> Unit,
) {
    val ap = view.you?.ap ?: 0
    val taken = view.you?.personalActions ?: emptyList()
    val locked = view.you?.ready == true
    BriefingPane(view.briefing, view.you?.team)
    PresenceCard(view)
    if (locked) {
        GlassCard(Modifier.fillMaxWidth(), Amber) {
            Text("TEAMACTIES VASTGELEGD", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(6.dp))
            Text("Wachten op resolutie… Dossier en chat blijven open.", color = Fog, fontSize = 14.sp, lineHeight = 20.sp)
            Spacer(Modifier.height(8.dp))
            GhostButton("Acties openen", onUnlock, Fog)
        }
    } else {
        Text("JOUW ACTIES  •  ${ap} AP", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        Text("De overkant wacht niet. Jij ook niet.", color = Fog, fontSize = 13.sp)
        view.availableActions.forEach { action ->
            ActionCard(
                action = action,
                selected = action.id in taken,
                enabled = action.id !in taken && ap >= action.ap,
                badge = "${action.ap} AP",
                onClick = { onPersonal(action.id) },
            )
        }
        Spacer(Modifier.height(4.dp))
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
        Spacer(Modifier.height(4.dp))
        GhostButton(if (locked) "Gereed" else "Vastleggen", onLock, Amber)
    }
}

@Composable
private fun PresenceCard(view: SessionView) {
    val ready = view.teamReady
    GlassCard(Modifier.fillMaxWidth(), Fog) {
        Text("TEAM", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(6.dp))
        val yours = if (view.you?.ready == true) "GEREED" else "NIET GEREED"
        Text("JOUW ACTIES  ·  $yours", color = Color.White, fontSize = 14.sp)
        if (ready != null) {
            Text("TEAM  ${ready.ready} / ${ready.total} spelers gereed", color = Fog, fontSize = 13.sp)
        }
        Text("TEGENSTANDER  ·  ${view.opponentStatus ?: "RONDE ACTIEF"}", color = Fog, fontSize = 13.sp)
        if (view.teamPresence.isNotEmpty()) {
            Spacer(Modifier.height(6.dp))
            view.teamPresence.forEach { p ->
                Text("${p.name}  ·  ${p.status}", color = Color.White, fontSize = 13.sp)
            }
        }
    }
}

@Composable
private fun ImpactOverlay(items: List<Impact>, onAck: () -> Unit) {
    Box(Modifier.fillMaxSize().background(Color.Black.copy(0.82f)).padding(22.dp), contentAlignment = Alignment.Center) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("VIJANDIGE DRUK", color = PaperRed, letterSpacing = 3.sp, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            items.forEach { impact ->
                GlassCard(Modifier.fillMaxWidth(), if (impact.kind == "conflict") PaperRed else Amber) {
                    Text((impact.title ?: "").uppercase(), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp, lineHeight = 22.sp)
                    Spacer(Modifier.height(8.dp))
                    Text(impact.body ?: "", color = Fog, fontSize = 15.sp, lineHeight = 22.sp)
                }
            }
            GhostButton("Gezien", onAck, Amber)
        }
    }
}

@Composable
private fun ConsequenceOverlay(
    view: SessionView,
    onFollowUp: (String) -> Unit,
    onDismiss: () -> Unit,
    busy: Boolean,
) {
    val result = view.result ?: return
    Box(Modifier.fillMaxSize().background(Color.Black.copy(0.88f)).padding(18.dp)) {
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("GEVOLGEN", color = Amber, letterSpacing = 3.sp, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Text(result.headline ?: "De kade antwoordt.", color = Color.White, fontFamily = FontFamily.Serif, fontSize = 22.sp, lineHeight = 28.sp)
            result.beats.forEach { beat ->
                GlassCard(Modifier.fillMaxWidth(), Amber) {
                    Text((beat.cause ?: "").uppercase(), color = Amber, fontSize = 11.sp, letterSpacing = 1.sp, fontWeight = FontWeight.Bold)
                    Text(beat.effect ?: "", color = Color(0xFFEDE6DA), fontSize = 15.sp, lineHeight = 22.sp)
                    if (beat.evidenceDelta != 0 || beat.heatDelta != 0) {
                        Text(
                            listOfNotNull(
                                beat.evidenceDelta.takeIf { it != 0 }?.let { "Evidence ${signed(it)}" },
                                beat.heatDelta.takeIf { it != 0 }?.let { "Heat ${signed(it)}" },
                            ).joinToString("    "),
                            color = Color.White,
                            fontSize = 12.sp,
                        )
                    }
                }
            }
            DeltaMeter("EVIDENCE", result.evidenceOld, result.evidenceDelta, result.evidenceScore, Ice)
            DeltaMeter("HEAT", result.heatOld, result.heatDelta, result.heat, PaperRed)
            val followUps = result.followUps
            if (followUps.isNotEmpty() && view.you?.followUpTaken != true) {
                Text("WAT JE NU KUNT DOEN", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                followUps.forEach { fu ->
                    FollowUpCard(fu, enabled = !busy) { onFollowUp(fu.id) }
                }
            } else if (view.you?.followUpTaken == true) {
                Text("Vervolg vastgelegd.", color = Fog, fontSize = 13.sp)
            }
            GhostButton("Begrepen", onDismiss, Amber, !busy)
        }
    }
}

@Composable
private fun FollowUpCard(fu: FollowUp, enabled: Boolean, onClick: () -> Unit) {
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, Amber.copy(0.5f), RoundedCornerShape(12.dp))
            .background(Amber.copy(0.12f))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(14.dp),
    ) {
        Column {
            Text((fu.label ?: fu.id).uppercase(), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            if (!fu.hint.isNullOrBlank()) Text(fu.hint, color = Fog, fontSize = 13.sp, lineHeight = 18.sp)
        }
    }
}

@Composable
private fun DeltaMeter(label: String, old: Int, delta: Int, now: Int, color: Color) {
    val progress by animateFloatAsState((now.coerceIn(0, 100)) / 100f, tween(700), label = label)
    Column(Modifier.fillMaxWidth()) {
        Text(
            "$label  $old  →  ${signed(delta)}  →  $now",
            color = color,
            letterSpacing = 1.5.sp,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
        )
        Spacer(Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { progress },
            modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(99.dp)),
            color = color,
            trackColor = Color.White.copy(0.08f),
        )
    }
}

private fun signed(value: Int) = if (value > 0) "+$value" else "$value"

@Composable
private fun BriefingPane(text: String?, team: String?) {
    GlassCard(Modifier.fillMaxWidth(), teamAccent(team)) {
        SectionTitle(if (team == "mafia") "PRIVÉ — MAFFIA" else "DOSSIER — RECHERCHE", teamAccent(team))
        Text(text ?: "Wachten op briefing…", color = Color(0xFFEDE6DA), fontSize = 15.sp, lineHeight = 22.sp)
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
        Text(result?.headline ?: "De nacht houdt haar mond.", color = Color.White, fontFamily = FontFamily.Serif, fontSize = 20.sp, lineHeight = 26.sp)
        Spacer(Modifier.height(10.dp))
        result?.beats.orEmpty().forEach { beat ->
            Text(beat.cause ?: "", color = Amber, fontSize = 12.sp, letterSpacing = 1.sp, fontWeight = FontWeight.Bold)
            Text(beat.effect ?: "", color = Fog, fontSize = 14.sp, lineHeight = 20.sp)
            if (!beat.cinematic.isNullOrBlank()) {
                Text(
                    "CINEMATIC OPNIEUW",
                    color = Fog,
                    fontSize = 11.sp,
                    letterSpacing = 2.sp,
                    modifier = Modifier.clickable {
                        onReplay(CinematicCue(id = beat.cinematic, title = beat.cause, kind = "replay"))
                    },
                )
            }
            Spacer(Modifier.height(8.dp))
        }
        DeltaMeter("EVIDENCE", result?.evidenceOld ?: 0, result?.evidenceDelta ?: 0, view.evidenceScore, Ice)
        Spacer(Modifier.height(8.dp))
        DeltaMeter("HEAT", result?.heatOld ?: 0, result?.heatDelta ?: 0, view.heat, PaperRed)
        Spacer(Modifier.height(10.dp))
        Text(
            "MAFFIA ${view.scores?.mafia ?: 0}    ·    DETECTIVES ${view.scores?.detective ?: 0}",
            color = Color.White,
            letterSpacing = 1.5.sp,
            fontSize = 13.sp,
        )
        if (finale) {
            Spacer(Modifier.height(16.dp))
            Text("DE STAD SLAAPT NOOIT.", color = PaperRed, letterSpacing = 3.sp, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            Text("VOLGENDE ZAAK — BINNENKORT", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp)
        }
    }
}

@Composable
private fun InboxPane(view: SessionView) {
    GlassCard(Modifier.fillMaxWidth(), Fog) {
        SectionTitle("ONTWIKKELINGEN", Amber)
        val items = view.developments
        if (items.isEmpty()) {
            Text("Nog geen ontwikkelingen. De kade is stil.", color = Fog, fontSize = 14.sp)
        } else {
            items.reversed().forEach { item ->
                val clock = item.at?.substringAfter("T")?.take(5) ?: "—"
                Text("$clock  ·  ${(item.title ?: "").uppercase()}", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                if (!item.body.isNullOrBlank()) Text(item.body, color = Fog, fontSize = 13.sp, lineHeight = 18.sp)
                Spacer(Modifier.height(8.dp))
            }
        }
    }
}

@Composable
private fun CaseDossier(view: SessionView, onShare: (String) -> Unit, onReplay: (CinematicCue) -> Unit) {
    GlassCard(Modifier.fillMaxWidth(), Ice) {
        SectionTitle("ZAAKDOSSIER", Ice)
        view.clues.forEach { clue ->
            ClueCard(clue, onShare, onReplay)
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun ClueCard(clue: Clue, onShare: (String) -> Unit, onReplay: (CinematicCue) -> Unit) {
    val ctx = LocalContext.current
    val thumb = CinematicCatalog.thumbRes(ctx, clue.cinematic)
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
        if (clue.status != "unknown") {
            Text("Gevonden tijdens  •  ${clue.foundDuring ?: "—"}", color = Fog.copy(0.8f), fontSize = 11.sp)
            Text("Betrouwbaarheid  ${clue.reliability}%", color = Amber, fontSize = 11.sp)
        }
        if (clue.related.isNotEmpty()) {
            Text("Gerelateerd  •  ${clue.related.joinToString(" · ")}", color = Ice, fontSize = 11.sp)
        }
        if (clue.status != "unknown") {
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
        if (ops.locations.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text("LOCATIES", color = Amber, fontSize = 11.sp, letterSpacing = 2.sp)
            ops.locations.forEach { Text("•  $it", color = Fog, fontSize = 14.sp) }
        }
        Spacer(Modifier.height(8.dp))
        Text("HEAT  ${ops.heat}", color = PaperRed, fontSize = 12.sp, letterSpacing = 1.sp)
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
            .heightIn(min = 96.dp, max = 168.dp)
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
    "play", "briefing", "huddle", "personal", "action" -> "De nacht is open"
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
