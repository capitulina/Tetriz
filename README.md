# Tetris com Álgebra Linear

Este repositório junta um **Tetris didático em Python** com um texto curto sobre a matemática por trás da rotação das peças.

No jogo, cada peça tem um **pivô** na grade e blocos descritos por **offsets** em relação a esse ponto. Ao apertar **W**, a rotação não usa só a matriz $R(90°)$ — que gira em torno da origem $(0,0)$ — e sim a composição

$$M = T_{\text{volta}} \cdot R(90°) \cdot T_{\text{ida}}$$

em coordenadas homogêneas $3 \times 3$: transladar o pivô para a origem, girar e devolver o pivô. Assim, a peça gira no lugar certo, como no Tetris clássico.

O código está em `tetriz.py` . O artigo em `tetris_algebra_linear.tex` explica o fluxo passo a passo.

## Gameplay

Assista ao vídeo do jogo rodando:

**[▶︎](https://youtu.be/MKADu6Np390?si=kqw6QCprTsLTHVN_)**
