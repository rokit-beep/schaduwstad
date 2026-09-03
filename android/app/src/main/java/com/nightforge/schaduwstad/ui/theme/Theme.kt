package com.nightforge.schaduwstad.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val Ink = Color(0xFF070709)
val PaperRed = Color(0xFFB4232C)
val Amber = Color(0xFFC9A36A)
val Steel = Color(0xFF1C2A3A)
val Ice = Color(0xFF7EA4C9)
val Fog = Color(0xFFB9B3A9)
val Glass = Color(0xCC120F12)

val MafiaBrush = Brush.verticalGradient(listOf(Color(0xFF2A0A0C), Ink))
val DetectiveBrush = Brush.verticalGradient(listOf(Color(0xFF0B1624), Ink))
val NightBrush = Brush.verticalGradient(listOf(Color(0xFF14080C), Color(0xFF070812), Ink))

private val Scheme = darkColorScheme(
    primary = PaperRed,
    onPrimary = Color.White,
    secondary = Ice,
    background = Ink,
    surface = Color(0xFF121014),
    onBackground = Color(0xFFF3EDE4),
    onSurface = Color(0xFFF3EDE4),
    error = PaperRed,
)

@Composable
fun SchaduwstadTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = Scheme,
        typography = MaterialTheme.typography.copy(
            displayLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 42.sp, letterSpacing = 2.sp, color = Color.White),
            headlineMedium = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, letterSpacing = 1.sp, color = Color.White),
            titleMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Medium, fontSize = 16.sp, letterSpacing = 1.4.sp, color = Fog),
            bodyLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = 16.sp, lineHeight = 24.sp, color = Color(0xFFE8E2D8)),
            bodyMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontSize = 14.sp, lineHeight = 20.sp, color = Fog),
            labelLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Bold, fontSize = 13.sp, letterSpacing = 2.sp, color = Color.White),
        ),
        content = content,
    )
}

fun teamAccent(team: String?): Color = when (team) {
    "mafia" -> PaperRed
    "detective" -> Ice
    else -> Amber
}
