# ImageLab PDI

Aplicação desktop da disciplina **Introdução ao Processamento Digital de Imagens**
(UFPB, 2026.1). Ela recebe imagens PNG em tons de cinza ou RGB, executa os
processos obrigatórios da disciplina, exibe resultados e métricas e permite salvar
cada resultado como PNG. Equipe: Erik Freire, Klayvert de Andrade, Nicolas Passos e
Thaís Melquíades.

## Requisitos e execução no Windows

Requer Windows, Python 3.11 e PowerShell. O fluxo reproduzível recomendado é:

```powershell
git clone <URL-DO-REPOSITORIO>
Set-Location digital-image-processing
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\scripts\run.ps1
```

Também é possível iniciar diretamente com ` .\.venv\Scripts\python.exe -m imagelab`.
O aplicativo aceita somente PNG **L de 8 bits** e **RGB de 24 bits**. Ele rejeita
RGBA, paleta, CMYK e formatos não PNG com uma mensagem orientativa. A imagem de
origem nunca é modificada e a exportação não permite sobrescrevê-la.

Problemas comuns:

- `py` não encontrado: instale Python 3.11 pelo instalador oficial e marque a opção
  para adicioná-lo ao PATH.
- Falha de Qt em teste automatizado: execute ` $env:QT_QPA_PLATFORM='offscreen' ` antes
  do pytest em ambiente sem desktop.
- O script informa `.venv` ausente: execute primeiro as etapas de criação e instalação.
- Um processo indisponível: verifique o modo de imagem; equalização, limiarização e
  fatiamento são operações exclusivamente em tons de cinza.

## Uso da bancada

1. Abra uma imagem PNG.
2. Escolha um processo no painel. Operações incompatíveis ficam desabilitadas e
   explicam a razão.
3. Ajuste somente os parâmetros mostrados e clique em **Processar**.
4. Analise a imagem de resultado, métricas, duração e abas de resultados acessórios.
5. Salve o resultado principal ou um acessório individualmente.

O painel de processo sempre identifica a entrada como a **imagem original carregada**.
Use **Ajustar**, o controle deslizante de zoom, `+`, `−` ou `Ctrl` + roda do mouse para
navegação da imagem; quando ampliada, arraste-a para deslocar a visualização. As
métricas comparam original e resultado, e os resultados acessórios aparecem em uma aba
própria quando disponíveis. Processamentos ocorrem em worker separado: enquanto a ação
mostra **Processando…**, controles concorrentes ficam desabilitados e a aplicação
continua responsiva.

O procedimento detalhado de operação, demonstração e validação está em
[docs/guia-de-uso-e-testes.md](docs/guia-de-uso-e-testes.md).

## Processos e compatibilidade

| Categoria | Processos | Modos |
|---|---|---|
| Decomposições | RGB; HSV convencional | RGB |
| Intensidade | Limiarização, logarítmica, potência/gama, fatiamento, equalização | Limiarização, fatiamento e equalização: L; log/gama: L e RGB |
| Filtros espaciais | Gaussiano, mediana, mínimo, máximo, mediana adaptativa | L e RGB por canal |
| Realce e bordas | Máscara de aguçamento, Laplaciano, Sobel | L e RGB por canal |
| Frequência | Gaussiano PB/PA, Butterworth PB/PA | L e RGB por canal |
| Ruídos | Gaussiano, sal, pimenta, sal e pimenta | L e RGB |

Parâmetros principais:

- Janelas espaciais: ímpares entre 3 e 31 e não maiores que a menor dimensão da imagem.
- Gaussiano espacial: `sigma > 0`; kernel normalizado.
- Aguçamento: ganho não negativo, `resultado = original + ganho × (original - gaussiana)`.
- Laplaciano e Sobel: janelas 3, 5 ou 7; Sobel usa `|Gx| + |Gy|`.
- Frequência: `D0` pode ser informado em bins da FFT preenchida ou como `D0/Dmax`.
  Butterworth aceita ordem inteira `n` de 1 a 20.
- Ruído gaussiano: média `mu` em `[-255, 255]` e desvio padrão `sigma` em `[0,255]`.
  Densidades e proporção de sal ficam em `[0,1]`.

## Convenções matemáticas que afetam o resultado

- **HSV:** a decomposição usa HSV convencional, não HSI. H é calculado em graus no
  intervalo `[0,360)` e mapeado para `[0,255]`; S e V também são mapeados para
  `[0,255]`. A aba H alerta que matiz é uma grandeza circular.
- **Arredondamento e clipping:** operações contínuas preservam `float64` até a borda
  de exportação; então usam arredondamento half-up, clipping em `[0,255]` e `uint8`.
- **Equalização:** LUT `floor(255 × CDF + 0,5)`, sem subtrair `CDF_min`.
- **Bordas espaciais:** `BORDER_REFLECT_101`, equivalente a `np.pad(..., mode='reflect')`.
- **Laplaciano:** derivadas em `CV_64F`; resultado realçado é `original - L` e o
  acessório ajustado usa uma escala global única em RGB.
- **Frequência:** para uma imagem `M × N`, usa padding de zeros `P=2M`, `Q=2N`, FFT
  centralizada, IFFT real e recorte superior esquerdo. O padding reduz, mas não
  elimina matematicamente, wraparound. Gaussiano PB é
  `exp(-D²/(2D0²))`; PA é seu complemento. Butterworth PB é
  `1/(1+(D/D0)^(2n))`; PA é seu complemento estável.
- **Ruídos:** o gaussiano é independente por componente RGB. Impulsos escolhem sem
  reposição `floor(densidade × pixels + 0,5)` coordenadas; em RGB alteram o pixel
  inteiro para preto ou branco. Sal e pimenta divide o total pela proporção de sal
  com o mesmo arredondamento.

## Amostras e roteiro de demonstração

As imagens em [`assets/samples`](assets/samples) cobrem constante, impulso, degrau,
gradiente, blocos RGB e gradiente ruidoso. Para recriá-las:

```powershell
.\.venv\Scripts\python.exe scripts\generate_samples.py
```

Roteiro sugerido para a apresentação:

1. Abra `noisy-gradient.png`; aplique sal e pimenta com densidade `0,15` e, em
   seguida, mediana `3×3`. Explique por que a mediana remove ruído impulsivo.
2. Abra `gradient.png`; aplique transformação gama com `gamma=0,5`. Explique a
   diferença entre clarear intensidades baixas e aplicar ganho linear.
3. Abra `rgb-blocks.png`; execute HSV e explique os canais H, S e V.
4. Abra `step.png`; compare Sobel `3×3` e Laplaciano `3×3`.
5. Abra `impulse.png`; compare passa-baixa Gaussiano e Butterworth usando corte
   normalizado `0,25`, com ordem Butterworth `4`.

Perguntas conceituais para ensaio: por que H é circular; por que RGB é processado
por canal; por que o padding de frequência não zera todo wraparound; qual política
de borda é usada; e por que ruído gaussiano e sal-e-pimenta exigem filtros diferentes.

## Qualidade e desenvolvimento

Execute todos os gates antes de entregar:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m ruff format src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest --cov=imagelab --cov-report=term-missing -q
```

O código separa modelos e algoritmos (`core`), orquestração (`application`), I/O
(`infrastructure`) e widgets PySide6 (`ui`). O catálogo de processos é a fonte única
de nomes, categorias, compatibilidade, parâmetros e executores.

Um executável PyInstaller pode ser produzido como conveniência adicional, mas o
caminho oficial e validado de execução continua sendo o ambiente Python acima.

## Referências

- Slides da disciplina: *Imagens coloridas*, *Transformações de intensidade e
  filtragem espacial* e *Filtragem no domínio da frequência*.
- R. C. Gonzalez e R. E. Woods, *Digital Image Processing*, 4ª ed.
- [OpenCV — filtros espaciais, Sobel e Laplaciano](https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html).
- [SciPy `ndimage`](https://docs.scipy.org/doc/scipy/reference/ndimage.html).
- H. Hwang e R. A. Haddad, [Adaptive Median Filters: New Algorithms and Results](https://doi.org/10.1109/83.370679).
- [scikit-image `random_noise`](https://scikit-image.org/docs/stable/api/skimage.util.html#skimage.util.random_noise).
