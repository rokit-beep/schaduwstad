package com.nightforge.schaduwstad.ui.lobby

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nightforge.schaduwstad.ui.components.CinematicBackdrop
import com.nightforge.schaduwstad.ui.components.ConnectionPill
import com.nightforge.schaduwstad.ui.components.ErrorBanner
import com.nightforge.schaduwstad.ui.components.GhostButton
import com.nightforge.schaduwstad.ui.components.GlassCard
import com.nightforge.schaduwstad.ui.components.SectionTitle
import com.nightforge.schaduwstad.ui.components.TeamChip
import com.nightforge.schaduwstad.ui.theme.Amber
import com.nightforge.schaduwstad.ui.theme.Fog
import com.nightforge.schaduwstad.ui.theme.Ice
import com.nightforge.schaduwstad.ui.theme.PaperRed
import com.nightforge.schaduwstad.viewmodel.UiState

@Composable
fun LobbyScreen(
    state: UiState,
    reconnecting: Boolean,
    onMafia: () -> Unit,
    onDetective: () -> Unit,
    onReady: () -> Unit,
    onStart: () -> Unit,
    onLeave: () -> Unit,
) {
    val view = state.view
    val ctx = LocalContext.current
    val haptics = LocalHapticFeedback.current
    val code = view?.lobbyCode ?: state.joinCode
    val cap = view?.teamSize?.cap ?: 6
    CinematicBackdrop(dim = 0.7f) {
        Column(Modifier.fillMaxSize().padding(20.dp)) {
            ConnectionPill(state.connected, reconnecting)
            Spacer(Modifier.height(12.dp))
            SectionTitle("LOBBY")
            Text(code, color = Color.White, fontFamily = FontFamily.Serif, fontSize = 44.sp, letterSpacing = 8.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(6.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                Text("KOPIEER", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, modifier = Modifier.clickable {
                    haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                    val cm = ctx.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    cm.setPrimaryClip(ClipData.newPlainText("lobby", code))
                })
                Text("DEEL", color = Amber, letterSpacing = 2.sp, fontSize = 11.sp, modifier = Modifier.clickable {
                    ctx.startActivity(
                        Intent.createChooser(
                            Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_TEXT, "Schaduwstad lobby $code")
                            },
                            "Deel lobby",
                        ),
                    )
                })
            }
            Spacer(Modifier.height(16.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                GlassCard(Modifier.weight(1f), PaperRed) {
                    Text("MAFFIA", color = PaperRed, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text("${view?.teamSize?.mafia ?: 0}/$cap", color = Color.White, fontSize = 28.sp, fontFamily = FontFamily.Serif)
                }
                GlassCard(Modifier.weight(1f), Ice) {
                    Text("DETECTIVES", color = Ice, letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text("${view?.teamSize?.detective ?: 0}/$cap", color = Color.White, fontSize = 28.sp, fontFamily = FontFamily.Serif)
                }
            }
            Spacer(Modifier.height(12.dp))
            LazyColumn(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(view?.players ?: emptyList(), key = { it.id }) { p ->
                    GlassCard(Modifier.fillMaxWidth(), if (p.ready) Amber else Fog) {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                            Column {
                                Text(p.name + if (p.isYou) "  (jij)" else "", color = Color.White, fontWeight = FontWeight.Medium)
                                TeamChip(p.team)
                            }
                            Text(
                                buildString {
                                    if (p.isHost) append("HOST  ")
                                    append(if (p.ready) "READY" else "WACHT")
                                },
                                color = if (p.ready) Amber else Fog,
                                fontSize = 11.sp,
                                letterSpacing = 1.5.sp,
                            )
                        }
                    }
                }
            }
            ErrorBanner(state.error)
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(Modifier.weight(1f)) { GhostButton("Maffia", onMafia, PaperRed) }
                Box(Modifier.weight(1f)) { GhostButton("Detectives", onDetective, Ice) }
            }
            Spacer(Modifier.height(8.dp))
            GhostButton(if (view?.you?.ready == true) "Niet ready" else "Ready", onReady, Amber, view?.you?.team != null && !state.busy)
            Spacer(Modifier.height(8.dp))
            if (view?.you?.isHost == true) {
                GhostButton("Start zaak", onStart, PaperRed, view.canStart && !state.busy)
                Spacer(Modifier.height(8.dp))
            }
            GhostButton("Verlaten", onLeave, Fog)
        }
    }
}
