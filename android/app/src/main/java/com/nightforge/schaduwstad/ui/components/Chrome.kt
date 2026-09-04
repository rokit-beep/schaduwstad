package com.nightforge.schaduwstad.ui.components

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nightforge.schaduwstad.R
import com.nightforge.schaduwstad.ui.theme.Amber
import com.nightforge.schaduwstad.ui.theme.Fog
import com.nightforge.schaduwstad.ui.theme.Glass
import com.nightforge.schaduwstad.ui.theme.Ink
import com.nightforge.schaduwstad.ui.theme.PaperRed
import com.nightforge.schaduwstad.ui.theme.teamAccent

@Composable
fun CinematicBackdrop(modifier: Modifier = Modifier, dim: Float = 0.62f, content: @Composable () -> Unit) {
    Box(modifier.fillMaxSize().background(Ink)) {
        Image(
            painter = painterResource(R.drawable.intro_poster),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
        )
        Box(Modifier.fillMaxSize().background(Color.Black.copy(dim)))
        Box(
            Modifier.fillMaxSize().background(
                Brush.verticalGradient(listOf(Color.Transparent, Color.Black.copy(0.88f))),
            ),
        )
        content()
    }
}

@Composable
fun GhostButton(label: String, onClick: () -> Unit, accent: Color = PaperRed, enabled: Boolean = true) {
    val shape = RoundedCornerShape(4.dp)
    Box(
        Modifier
            .fillMaxWidth()
            .height(56.dp)
            .clip(shape)
            .border(1.dp, accent.copy(if (enabled) 0.7f else 0.25f), shape)
            .background(accent.copy(0.12f))
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(label.uppercase(), color = Color.White.copy(if (enabled) 1f else 0.4f), letterSpacing = 3.sp, fontWeight = FontWeight.Bold, fontSize = 13.sp)
    }
}

@Composable
fun ConnectionPill(connected: Boolean, reconnecting: Boolean) {
    val pulse by rememberInfiniteTransition(label = "pulse").animateFloat(
        0.45f, 1f,
        infiniteRepeatable(tween(1100, easing = LinearEasing), RepeatMode.Reverse),
        label = "a",
    )
    val color = when {
        reconnecting -> Amber
        connected -> Color(0xFF6FCF97)
        else -> Fog.copy(0.5f)
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(8.dp).clip(CircleShape).background(color.copy(if (reconnecting) pulse else 1f)))
        Spacer(Modifier.width(8.dp))
        Text(
            when {
                reconnecting -> "VERBINDING HERSTELLEN…"
                connected -> "SERVER  •  VERBONDEN"
                else -> "SERVER  ○  OFFLINE"
            },
            color = color,
            letterSpacing = 1.6.sp,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
        )
    }
}

@Composable
fun SectionTitle(text: String, accent: Color = Amber) {
    Column(Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
        Text(text.uppercase(), color = accent, letterSpacing = 4.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(6.dp))
        Box(Modifier.fillMaxWidth().height(1.dp).background(accent.copy(0.35f)))
    }
}

@Composable
fun BrandMark() {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text(
            "SCHADUWSTAD",
            color = Color.White,
            fontFamily = FontFamily.Serif,
            fontWeight = FontWeight.Bold,
            fontSize = 32.sp,
            letterSpacing = 2.sp,
            textAlign = TextAlign.Center,
            maxLines = 1,
            overflow = TextOverflow.Clip,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(6.dp))
        Text("VERTROUW. BEDRIEG. OVERLEEF.", color = PaperRed, letterSpacing = 3.sp, fontSize = 11.sp)
    }
}

@Composable
fun GlassCard(modifier: Modifier = Modifier, accent: Color = Fog, content: @Composable () -> Unit) {
    Box(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Glass)
            .border(1.dp, accent.copy(0.28f), RoundedCornerShape(16.dp))
            .padding(16.dp),
    ) { content() }
}

@Composable
fun ErrorBanner(message: String?) {
    if (message.isNullOrBlank()) return
    Box(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(PaperRed.copy(0.18f)).padding(12.dp),
    ) {
        Text(message, color = Color(0xFFFFC9C9), fontSize = 14.sp)
    }
}

@Composable
fun TeamChip(team: String?) {
    val label = when (team) {
        "mafia" -> "MAFFIA"
        "detective" -> "DETECTIVE"
        else -> "GEEN TEAM"
    }
    Text(label, color = teamAccent(team), letterSpacing = 2.sp, fontSize = 11.sp, fontWeight = FontWeight.Bold)
}
