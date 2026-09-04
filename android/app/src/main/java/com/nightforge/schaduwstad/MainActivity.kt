package com.nightforge.schaduwstad

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nightforge.schaduwstad.ui.game.GameScreen
import com.nightforge.schaduwstad.ui.intro.IntroScreen
import com.nightforge.schaduwstad.ui.lobby.LobbyScreen
import com.nightforge.schaduwstad.ui.menu.HowScreen
import com.nightforge.schaduwstad.ui.menu.JoinScreen
import com.nightforge.schaduwstad.ui.menu.MenuScreen
import com.nightforge.schaduwstad.ui.menu.NameScreen
import com.nightforge.schaduwstad.ui.menu.SettingsScreen
import com.nightforge.schaduwstad.ui.theme.SchaduwstadTheme
import com.nightforge.schaduwstad.viewmodel.Dest
import com.nightforge.schaduwstad.viewmodel.GameViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        setTheme(R.style.Theme_Schaduwstad)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SchaduwstadTheme {
                val vm: GameViewModel = viewModel()
                val state by vm.ui.collectAsState()
                val socket by vm.socketStatus.collectAsState()
                val reconnecting = socket.name == "RECONNECTING"
                Box(Modifier.fillMaxSize().systemBarsPadding()) {
                    when (state.dest) {
                        Dest.Intro -> IntroScreen(onFinished = vm::consumeIntro)
                        Dest.Menu -> MenuScreen(
                            state = state,
                            reconnecting = reconnecting,
                            onCreate = vm::createLobby,
                            onJoin = { vm.go(Dest.Join) },
                            onHow = { vm.go(Dest.How) },
                            onSettings = { vm.go(Dest.Settings) },
                        )
                        Dest.Name -> NameScreen(state.playerName, vm::saveName)
                        Dest.Join -> JoinScreen(state, vm::setJoinCode, vm::joinLobby) { vm.go(Dest.Menu) }
                        Dest.Settings -> SettingsScreen(
                            state = state,
                            onSave = vm::saveServer,
                            onReplay = vm::replayIntro,
                            onName = { vm.go(Dest.Name) },
                            onBack = { vm.go(Dest.Menu) },
                            onPing = vm::ping,
                        )
                        Dest.How -> HowScreen { vm.go(Dest.Menu) }
                        Dest.Lobby -> LobbyScreen(
                            state = state,
                            reconnecting = reconnecting,
                            onMafia = { vm.chooseTeam("mafia") },
                            onDetective = { vm.chooseTeam("detective") },
                            onReady = vm::toggleReady,
                            onStart = vm::startGame,
                            onLeave = vm::leaveToMenu,
                        )
                        Dest.Game -> GameScreen(
                            state = state,
                            reconnecting = reconnecting,
                            onDraft = vm::setChatDraft,
                            onSend = vm::sendChat,
                            onVote = vm::vote,
                            onPersonal = vm::personal,
                            onAdvance = vm::advance,
                            onLeave = vm::leaveToMenu,
                            onToggleDossier = vm::toggleDossier,
                            onShareClue = vm::shareClue,
                            onReplay = vm::replayCinematic,
                            onCinematicFinished = vm::cinematicFinished,
                        )
                    }
                }
            }
        }
    }
}
