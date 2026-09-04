package com.nightforge.schaduwstad.ui.menu

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nightforge.schaduwstad.ui.components.BrandMark
import com.nightforge.schaduwstad.ui.components.CinematicBackdrop
import com.nightforge.schaduwstad.ui.components.ConnectionPill
import com.nightforge.schaduwstad.ui.components.ErrorBanner
import com.nightforge.schaduwstad.ui.components.GhostButton
import com.nightforge.schaduwstad.ui.components.SectionTitle
import com.nightforge.schaduwstad.ui.theme.Amber
import com.nightforge.schaduwstad.ui.theme.Fog
import com.nightforge.schaduwstad.ui.theme.Ice
import com.nightforge.schaduwstad.ui.theme.PaperRed
import com.nightforge.schaduwstad.viewmodel.Dest
import com.nightforge.schaduwstad.viewmodel.UiState

@Composable
fun MenuScreen(
    state: UiState,
    reconnecting: Boolean,
    onCreate: () -> Unit,
    onJoin: () -> Unit,
    onHow: () -> Unit,
    onSettings: () -> Unit,
) {
    val haptics = LocalHapticFeedback.current
    CinematicBackdrop {
        Column(
            Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            ConnectionPill(state.connected, reconnecting)
            BrandMark()
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ErrorBanner(state.error)
                GhostButton("Nieuwe lobby", { haptics.performHapticFeedback(HapticFeedbackType.LongPress); onCreate() }, PaperRed, !state.busy)
                GhostButton("Lobby joinen", { haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove); onJoin() }, Ice, !state.busy)
                GhostButton("Hoe werkt het", onHow, Amber)
                GhostButton("Instellingen", onSettings, Fog)
                if (state.playerName.isNotBlank()) {
                    Text("SPELER  •  ${state.playerName.uppercase()}", color = Fog, letterSpacing = 2.sp, fontSize = 11.sp)
                }
            }
        }
    }
}

@Composable
fun NameScreen(current: String, onSave: (String) -> Unit) {
    var name by remember { mutableStateOf(current) }
    CinematicBackdrop {
        Column(Modifier.fillMaxSize().padding(24.dp).imePadding(), verticalArrangement = Arrangement.Center) {
            SectionTitle("IDENTITEIT")
            Text("Kies een naam. De stad onthoudt wie je bent — tot iemand anders het doet.", color = Fog, fontSize = 15.sp)
            Spacer(Modifier.height(20.dp))
            DarkField(name, { name = it.take(20) }, "Spelersnaam")
            Spacer(Modifier.height(20.dp))
            GhostButton("Betreed de stad", { onSave(name.trim()) }, PaperRed, name.trim().length >= 2)
        }
    }
}

@Composable
fun JoinScreen(state: UiState, onCode: (String) -> Unit, onJoin: () -> Unit, onBack: () -> Unit) {
    CinematicBackdrop {
        Column(Modifier.fillMaxSize().padding(24.dp).imePadding(), verticalArrangement = Arrangement.Center) {
            SectionTitle("LOBBY JOINEN", Ice)
            DarkField(state.joinCode, onCode, "Code", KeyboardCapitalization.Characters)
            Spacer(Modifier.height(16.dp))
            ErrorBanner(state.error)
            Spacer(Modifier.height(12.dp))
            GhostButton("Deelnemen", onJoin, Ice, state.joinCode.length == 4 && !state.busy)
            Spacer(Modifier.height(10.dp))
            GhostButton("Terug", onBack, Fog)
        }
    }
}

@Composable
fun SettingsScreen(state: UiState, onSave: (String, Int) -> Unit, onReplay: () -> Unit, onName: () -> Unit, onBack: () -> Unit, onPing: () -> Unit) {
    var host by remember(state.host) { mutableStateOf(state.host) }
    var port by remember(state.port) { mutableStateOf(state.port.toString()) }
    CinematicBackdrop {
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp).imePadding()) {
            SectionTitle("INSTELLINGEN")
            ConnectionPill(state.connected, false)
            Spacer(Modifier.height(16.dp))
            DarkField(host, { host = it }, "Serveradres (Tailscale)")
            Spacer(Modifier.height(10.dp))
            DarkField(port, { port = it.filter(Char::isDigit).take(5) }, "Poort", KeyboardCapitalization.None, KeyboardType.Number)
            Spacer(Modifier.height(16.dp))
            GhostButton("Opslaan & testen", {
                onSave(host, port.toIntOrNull() ?: 8098)
                onPing()
            }, Amber)
            Spacer(Modifier.height(10.dp))
            GhostButton("Naam wijzigen", onName, Fog)
            Spacer(Modifier.height(10.dp))
            GhostButton("Intro opnieuw bekijken", onReplay, PaperRed)
            Spacer(Modifier.height(10.dp))
            GhostButton("Terug", onBack, Fog)
            Spacer(Modifier.height(18.dp))
            Text("Poort 8098 is NightForge. Crime en Schaduwstad delen deze server. OpenNight (4520) blijft onaangeroerd.", color = Fog, fontSize = 13.sp)
        }
    }
}

@Composable
fun HowScreen(onBack: () -> Unit) {
    CinematicBackdrop(dim = 0.72f) {
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp)) {
            SectionTitle("HOE WERKT HET")
            HowBlock("MAFFIA", "Bescherm de organisatie.\nMisleid de recherche.\nBeheer je sporen.", PaperRed)
            Spacer(Modifier.height(14.dp))
            HowBlock("DETECTIVES", "Verzamel bewijs.\nWerk samen.\nOntmasker de organisatie.", Ice)
            Spacer(Modifier.height(14.dp))
            HowBlock("DAG 1", "Briefing, teamoverleg, 2 actiepunten voor persoonlijke zetten, daarna één teamstrategie. De server beslist. Cinematics volgen de uitkomst — nooit andersom.", Amber)
            Spacer(Modifier.height(14.dp))
            HowBlock("VERTROUW NIEMAND", "Teamchat en dossiers lekken nooit naar de overkant. Later kunnen verborgen rollen zelfs binnen je eigen team gevaarlijk worden.", Fog)
            Spacer(Modifier.height(22.dp))
            GhostButton("Begrepen", onBack, Fog)
        }
    }
}

@Composable
private fun HowBlock(title: String, body: String, accent: Color) {
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text(title, color = accent, letterSpacing = 3.sp, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, fontSize = 13.sp)
        Spacer(Modifier.height(8.dp))
        Text(body, color = Color(0xFFE6DFD4), fontSize = 16.sp, lineHeight = 24.sp)
    }
}

@Composable
fun DarkField(
    value: String,
    onValue: (String) -> Unit,
    label: String,
    caps: KeyboardCapitalization = KeyboardCapitalization.Words,
    type: KeyboardType = KeyboardType.Text,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValue,
        label = { Text(label) },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
        keyboardOptions = KeyboardOptions(capitalization = caps, keyboardType = type),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = Amber,
            unfocusedBorderColor = Fog.copy(0.4f),
            focusedLabelColor = Amber,
            unfocusedLabelColor = Fog,
            focusedTextColor = Color.White,
            unfocusedTextColor = Color.White,
            cursorColor = Amber,
        ),
    )
}
