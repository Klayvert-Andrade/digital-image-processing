# Guia de uso e validação — ImageLab PDI

Este guia descreve como iniciar, demonstrar e validar o ImageLab PDI em um
computador Windows.

## 1. Preparar o ambiente

Abra o PowerShell na pasta do projeto e execute:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

Se o ambiente já estiver preparado, basta iniciar:

```powershell
.\scripts\run.ps1
```

Alternativamente:

```powershell
.\.venv\Scripts\python.exe -m imagelab
```

## 2. Abrir e navegar pelas imagens

1. Clique em **Abrir PNG…**.
2. Escolha um PNG em tons de cinza de 8 bits ou RGB de 24 bits. Use as amostras em
   `assets\samples` para a apresentação.
3. A imagem carregada aparece à esquerda; o resultado do processo aparece à direita.
   As etiquetas abaixo de cada painel informam modo e dimensões.
4. Use **Ajustar**, o controle deslizante, `+`, `−` ou `Ctrl` + roda do mouse para
   enquadrar e ampliar a imagem.
5. Com a imagem ampliada, arraste-a com o botão esquerdo do mouse para deslocar a área
   visível.

A imagem original é preservada. Cada processo é executado novamente sobre ela, de
forma independente; salvar um resultado não altera o arquivo de origem.

## 3. Executar um processo

1. Escolha um processo no painel inferior esquerdo.
2. Leia a mensagem de compatibilidade. Processos incompatíveis ficam desabilitados.
3. Preencha os parâmetros exibidos. Unidades e limites aparecem junto aos controles.
4. Use **Restaurar padrões** para voltar aos valores recomendados.
5. Clique em **Processar**. O painel informa que a entrada é sempre a imagem original.
6. Enquanto o botão mostrar **Processando…**, uma nova execução e a abertura de outra
   imagem ficam bloqueadas para impedir resultados concorrentes ou obsoletos.
7. Ao finalizar, confira o resultado, as métricas comparativas, a duração e, quando
   houver, a aba **Resultados acessórios**.
8. Clique em **Salvar resultado…** para exportar o resultado principal. Nas abas de
   acessórios, use o botão correspondente para salvar cada canal ou imagem auxiliar.

## 4. O que demonstrar em cada categoria

| Etapa | Imagem sugerida | Processo e parâmetros | Verificação esperada |
|---|---|---|---|
| Ruído impulsivo | `noisy-gradient.png` | Sal e pimenta, densidade `0,15`; depois mediana `3×3` | A mediana reduz pontos pretos/brancos isolados. |
| Intensidade | `gradient.png` | Potência: `c=1`, `gamma=0,5` | Intensidades baixas ficam mais claras. |
| Cor | `rgb-blocks.png` | Decomposição HSV | H, S e V aparecem em abas; H é identificado como circular. |
| Bordas | `step.png` | Sobel `3×3`, depois Laplaciano `3×3` | A transição vertical produz resposta de borda. |
| Frequência | `impulse.png` | Butterworth passa-baixa, corte normalizado `0,25`, ordem `4` | O resultado mostra suavização controlada pela frequência de corte. |

Perguntas frequentes durante a avaliação:

- Por que a equalização, limiarização e fatiamento são exclusivos de tons de cinza?
- Por que H não deve ser interpretado como intensidade linear?
- Por que Sobel e Laplaciano em RGB são calculados por canal?
- Qual política de borda é utilizada? `BORDER_REFLECT_101` / `reflect`.
- Por que a FFT usa padding `2M × 2N` e por que isso apenas reduz wraparound?
- Qual a diferença entre ruído gaussiano e sal-e-pimenta?

## 5. Testar a aplicação manualmente

Use esta checklist antes da apresentação:

1. Abra `gradient.png` e confirme que são mostrados modo, largura e altura.
2. Tente selecionar limiarização para `rgb-blocks.png`; confirme que o processo fica
   indisponível e explica a incompatibilidade.
3. Execute os cinco processos da tabela anterior sem reiniciar o aplicativo.
4. Confirme que o botão de processar fica indisponível durante uma execução e volta ao
   normal ao final.
5. Teste zoom, ajuste e arraste em uma imagem ampliada.
6. Exporte um resultado para uma nova pasta e confirme que o PNG abre normalmente.
7. Execute RGB, HSV e Laplaciano e confirme a presença e a exportação dos acessórios.
8. Tente abrir um arquivo não PNG ou PNG RGBA e confirme que a janela continua aberta e
   mostra uma mensagem clara, sem traceback.
9. Redimensione a janela para aproximadamente 1280×720 e confirme que os painéis não
   se sobrepõem nem cortam controles importantes.

## 6. Executar os testes automatizados

No PowerShell, dentro da raiz do repositório:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m ruff format src tests scripts
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest --cov=imagelab --cov-report=term-missing -q
```

Resultado esperado:

- `ruff format`: nenhum arquivo inesperadamente reformulado;
- `ruff check`: `All checks passed!`;
- `mypy`: `Success: no issues found`;
- `pytest`: todos os testes passam e a cobertura global permanece acima de 80%.

Para investigar uma área isolada:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_noise.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_gaussian_frequency.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py -q
```

## 7. Conferência final de entrega

1. Execute `scripts\run.ps1` no computador que será usado na apresentação.
2. Gere novamente as amostras, se necessário, com
   `.\.venv\Scripts\python.exe scripts\generate_samples.py`.
3. Rode a checklist manual e os comandos automatizados.
4. Mantenha a pasta `assets\samples` e este guia disponíveis durante a demonstração.
5. Não exporte sobre o PNG de origem; escolha sempre outro nome ou diretório.
