package com.nightforge.schaduwstad.ui.cinematic

import android.view.ViewGroup
import androidx.annotation.OptIn
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.nightforge.schaduwstad.data.CinematicCue
import com.nightforge.schaduwstad.ui.theme.Amber
import kotlinx.coroutines.delay

@OptIn(UnstableApi::class)
@Composable
fun CinematicOverlay(
    queue: List<CinematicCue>,
    onFinished: () -> Unit,
) {
    if (queue.isEmpty()) return
    var intro by remember(queue) { mutableStateOf(true) }
    var index by remember(queue) { mutableStateOf(0) }
    if (intro) {
        LaunchedEffect(queue) {
            delay(1200)
            intro = false
        }
        Box(
            Modifier.fillMaxSize().background(Color.Black),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                "DE STAD REAGEERT…",
                color = Amber,
                letterSpacing = 4.sp,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Serif,
            )
        }
        return
    }
    val cue = queue.getOrNull(index)
    if (cue == null) {
        LaunchedEffect(Unit) { onFinished() }
        return
    }
    CinematicPlayer(
        cue = cue,
        next = queue.getOrNull(index + 1),
        onSkip = {
            if (index >= queue.lastIndex) onFinished() else index += 1
        },
    )
}

@OptIn(UnstableApi::class)
@Composable
fun CinematicPlayer(
    cue: CinematicCue,
    next: CinematicCue? = null,
    onSkip: () -> Unit,
    compact: Boolean = false,
) {
    val context = LocalContext.current
    val raw = CinematicCatalog.rawRes(context, cue.id)
    var visible by remember(cue.id) { mutableStateOf(false) }
    val alpha by animateFloatAsState(if (visible) 1f else 0f, tween(320), label = "cin")
    val player = remember {
        ExoPlayer.Builder(context).build().apply { volume = 1f }
    }
    val preload = remember {
        ExoPlayer.Builder(context).build().apply {
            volume = 0f
            playWhenReady = false
        }
    }
    val onSkipState = remember { mutableStateOf(onSkip) }
    onSkipState.value = onSkip
    val finishingState = remember { mutableStateOf(false) }
    fun finish() {
        if (finishingState.value) return
        finishingState.value = true
        visible = false
        player.pause()
        onSkipState.value()
    }
    LaunchedEffect(cue.id) {
        finishingState.value = true
        player.pause()
        player.clearMediaItems()
        finishingState.value = false
        visible = true
        if (raw == 0) {
            delay(900)
            finish()
            return@LaunchedEffect
        }
        val uri = android.net.Uri.parse("android.resource://${context.packageName}/$raw")
        player.setMediaItem(MediaItem.fromUri(uri))
        player.prepare()
        player.playWhenReady = true
        preload.pause()
        preload.clearMediaItems()
        next?.let { nxt ->
            CinematicCatalog.rawRes(context, nxt.id).takeIf { it != 0 }?.let { res ->
                preload.setMediaItem(
                    MediaItem.fromUri(android.net.Uri.parse("android.resource://${context.packageName}/$res")),
                )
                preload.prepare()
            }
        }
    }
    DisposableEffect(player) {
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(state: Int) {
                if (state == Player.STATE_ENDED) {
                    if (finishingState.value) return
                    finishingState.value = true
                    visible = false
                    onSkipState.value()
                }
            }
        }
        player.addListener(listener)
        onDispose {
            player.removeListener(listener)
            player.release()
            preload.release()
        }
    }
    Box(
        Modifier
            .fillMaxSize()
            .background(Color.Black)
            .alpha(alpha),
    ) {
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    this.player = player
                    useController = false
                    resizeMode = AspectRatioFrameLayout.RESIZE_MODE_FIT
                    setShutterBackgroundColor(android.graphics.Color.BLACK)
                    layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                    keepScreenOn = true
                }
            },
            update = { it.player = player },
            modifier = Modifier.fillMaxSize(),
        )
        Text(
            (cue.title ?: "").uppercase(),
            color = Color.White.copy(0.8f),
            letterSpacing = 2.sp,
            fontSize = if (compact) 11.sp else 13.sp,
            modifier = Modifier.align(Alignment.BottomStart).padding(22.dp),
        )
        Text(
            "OVERSLAAN",
            color = Color.White.copy(0.72f),
            letterSpacing = 3.sp,
            fontSize = 12.sp,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(22.dp)
                .clickable { finish() }
                .padding(8.dp),
        )
    }
}
