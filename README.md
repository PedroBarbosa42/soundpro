# SoundPro - Gerenciador & Baixador de Músicas e Playlists

O **SoundPro** é uma aplicação completa para busca, extração e download de músicas, vídeos e playlists do YouTube em alta qualidade. O sistema combina uma interface web moderna inspirada no Spotify com um motor avançado de processamento multimídia, realizando conversão automática de áudio para MP3 (192 kbps), injeção de metadados ID3 (título, artista, álbum) e inserção de capas em alta resolução diretamente nos arquivos baixados.

A aplicação pode ser utilizada localmente no computador via executável (.exe) ou acessada simultaneamente pelo celular conectado na mesma rede Wi-Fi ou pela nuvem.

---

## 📌 O Que a Aplicação Faz

- **Busca Integrada:** Permite pesquisar diretamente pelo nome da música ou artista, sem necessidade de abrir o YouTube para copiar links.
- **Suporte a Mídias e Playlists:** Processa vídeos individuais, músicas avulsas e playlists completas de dezenas ou centenas de faixas com um único clique.
- **Conversão de Alta Fidelidade (MP3 192 kbps):** Extrai a melhor faixa de áudio e a converte usando o motor FFmpeg.
- **Download em Vídeo (MP4):** Permite alternar instantaneamente para download em formato de vídeo MP4 em alta resolução.
- **Injeção Automática de Metadados ID3:** Insere título da música, nome do artista, álbum e incorpora a arte da capa em JPEG dentro do próprio arquivo MP3, garantindo que qualquer tocador (no carro, celular ou computador) exiba a capa e as informações corretas.
- **Acesso pelo Celular via QR Code:** O aplicativo transmite para a rede local; basta escanear o QR Code gerado na tela para controlar a aplicação e baixar as faixas diretamente para o smartphone.
- **Acompanhamento em Tempo Real:** Barra de progresso dinâmica com percentual, indicador de faixa atual/total e opção de cancelamento de download a qualquer momento.
- **Gerenciamento de Pastas de Destino:** Atalhos rápidos para as pastas padrão do sistema (*Músicas*, *Downloads*, *Área de Trabalho*) e seletor nativo de pastas.

---

## 🚀 Passo a Passo de Funcionamento

### 1. Inicialização
- Ao executar o aplicativo (`SoundPro.exe` ou `python app.py`), o servidor local inicializa e busca automaticamente uma porta TCP disponível (iniciando em `5000`).
- O navegador padrão do sistema é aberto automaticamente no endereço local seguro.
- O sistema detecta o IP do computador na rede local e disponibiliza a conexão para smartphones.

### 2. Pesquisa ou Colagem de Link
Na barra superior da interface, o usuário pode inserir:
- **Termo de busca comum:** Ex: `Coldplay - Yellow`, `Henrique e Juliano`. O sistema pesquisa no YouTube e traz os melhores resultados.
- **Link de vídeo/música:** Links normais (`https://www.youtube.com/watch?v=...`), links curtos (`youtu.be/...`) ou YouTube Music (`music.youtube.com/...`).
- **Link de playlist:** O sistema analisa a playlist, extrai todas as faixas, calcula durações e monta a lista de reprodução organizada.

### 3. Seleção de Formato e Pasta de Destino
- **Formato:** O usuário seleciona **MP3** (áudio de 192kbps) ou **MP4** (vídeo).
- **Pasta:** O usuário escolhe onde os arquivos serão salvos no computador (pastas rápidas *Músicas*, *Downloads*, *Desktop* ou clicando em *Procurar Outra...* para selecionar qualquer diretório).

### 4. Execução do Download
- **Download Individual:** Clicando no botão de download de qualquer faixa específica na lista ou grade de cards.
- **Download em Lote (Playlist Inteira):** Clicando em **Baixar Todas**, o sistema processa cada música sequencialmente sem travamento da interface gráfica.

### 5. Pós-Processamento Automático
Para cada faixa baixada em MP3:
1. O áudio original é extraído.
2. O **FFmpeg** converte o áudio para MP3 constante de 192kbps.
3. A arte da capa oficial em alta resolução é baixada.
4. A biblioteca `mutagen` grava as tags ID3v2 (título, artista, capa embutida no arquivo).
5. O arquivo final limpo e padronizado é movido para a pasta de destino selecionada.

### 6. Uso no Celular (Dispositivos Móveis)
1. Com o SoundPro aberto no computador, o usuário clica no botão **"No Celular"** no topo da tela.
2. Um modal se abre com um **QR Code** e o link direto da rede Wi-Fi (ex: `http://192.168.x.x:5000`).
3. Ao apontar a câmera do celular para o código, a interface completa abre no navegador do smartphone.
4. Ao baixar uma música pelo celular, o motor do PC faz a conversão pesada e a aplicação disponibiliza o botão **"Salvar no Aparelho"**, permitindo transferir o MP3 diretamente para a pasta de Downloads do próprio celular.
5. Pelo navegador do celular, o usuário pode selecionar *"Adicionar à tela de início"* para utilizar o SoundPro como um aplicativo em tela cheia.

---

## 📁 Estrutura de Arquivos

```text
├── app.py                     # Servidor Flask, gerenciador de rotas de API, rede local e SSE de progresso
├── logic.py                   # Motor de processamento (yt-dlp, FFmpeg, sanitização e injeção de ID3)
├── templates/
│   ├── index.html             # Interface web completa, responsiva, com estilos e lógica cliente (JS/CSS)
│   └── icone.ico              # Ícone oficial da aplicação
├── dist/
│   └── SoundPro.exe           # Executável portátil para Windows (não requer Python instalado)
├── ffmpeg/                    # Binários do FFmpeg para conversão de mídia
├── downloads/                 # Pasta de saída padrão para arquivos baixados
├── SoundPro.spec              # Configuração de compilação do executável com PyInstaller
├── requirements.txt           # Lista de dependências Python necessárias
├── Dockerfile                 # Configuração para implantação em containers na nuvem
├── Procfile                   # Instrução de inicialização para servidores em nuvem (Render, Heroku)
├── render.yaml                # Configuração de deploy automático no Render.com
└── COMO_PUBLICAR_NA_NUVEM.md  # Guia passo a passo para hospedar o app online gratuitamente
```

---

## ⚙️ Como Executar

### Opção 1: Via Executável Portátil (Windows)
1. Acesse a pasta `dist/`.
2. Dê dois cliques em `SoundPro.exe`.
3. O aplicativo abrirá automaticamente no navegador pronto para uso.

### Opção 2: Via Código Fonte (Python)
1. Certifique-se de ter o Python 3.10+ instalado.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o servidor:
   ```bash
   python app.py
   ```
4. O navegador abrirá automaticamente em `http://127.0.0.1:5000`.
