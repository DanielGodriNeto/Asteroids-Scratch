# Asteroids no Scratch

Remake do Asteroids (Atari, 1979) para o Scratch 3, com menu, configurações, créditos, recorde com iniciais e um estilo secreto Nyan Cat. Projeto da formação "Fundamentos de Lógica de Programação" do processo seletivo 2027–28 da Apple Developer Academy PUCPR.

## Entregas

- [`asteroids.sb3`](asteroids.sb3): o jogo. Abra em [scratch.mit.edu](https://scratch.mit.edu) → Arquivo → Carregar do seu computador.
- [`reflexao/Reflexao-Scratch-Daniel-Godri.pdf`](reflexao/Reflexao-Scratch-Daniel-Godri.pdf): a reflexão sobre o projeto.
- [`design/Desing-Apple-Daniel-Godri.pdf`](design/Desing-Apple-Daniel-Godri.pdf): a entrega da formação de Design de Interação (onboarding do Letterboxd).

## Como jogar

| Ação | Setas | WASD |
|---|---|---|
| Girar | ← → | A D |
| Acelerar | ↑ | W |
| Atirar | Espaço | Espaço |
| Hiperespaço | ↓ | S |

## Estrutura

- `build_sb3.py`, `sb3.py`, `assets.py`, `aseprite.py`: geram o `asteroids.sb3` (blocos, figurinos e sons).
- `art/`: pixel art em Aseprite (novelos de lã e o cachorro no disco voador).
- `test_game.js`: teste de ponta a ponta no scratch-vm.
- `reflexao/`: fonte HTML da reflexão, capturas de tela e o PDF.

```bash
npm install
npm test
```

## Créditos

Daniel Godri Neto. Baseado em Asteroids (Atari, 1979). O estilo "nyan" é uma homenagem de fã ao Nyan Cat, de Chris Torres.
