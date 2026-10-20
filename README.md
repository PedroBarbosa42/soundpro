# SoundPro - Gerenciador & Baixador de Músicas e Playlists para Desktop

O **SoundPro** é uma aplicação completa para Windows focada na busca, extração e download de músicas, vídeos e playlists do YouTube em alta fidelidade. O sistema combina uma interface moderna inspirada no Spotify rodando diretamente no navegador com um motor local de processamento multimídia, realizando conversão automática para MP3 (192 kbps), injeção de metadados ID3 (título, artista, álbum) e inserção de capas em alta definição diretamente nos arquivos baixados no computador.

A aplicação funciona de forma 100% local, autônoma e portátil através do executável **`SoundPro.exe`**.

---

## 📌 Principais Recursos

- **Busca Integrada:** Pesquise diretamente pelo nome da música ou artista, sem precisar abrir o YouTube para copiar links.
- **Suporte a Playlists e Mídias Individuais:** Baixe vídeos avulsos ou playlists inteiras com dezenas de faixas de uma só vez.
- **Conversão de Alta Fidelidade (MP3 192 kbps):** Extrai o áudio e converte em MP3 cristalino usando o motor embutido do FFmpeg.
- **Download em Vídeo (MP4):** Alterne facilmente para baixar o vídeo completo em alta resolução.
- **Tags ID3 e Capas Automáticas:** Incorpora automaticamente título, artista, álbum e a capa oficial em JPEG no arquivo MP3.
- **Acesso Rápido aos Arquivos:** Botão **"Abrir Pasta"** na barra superior e no player para abrir o Windows Explorer diretamente no diretório onde as músicas foram salvas.
- **Seleção de Pastas:** Atalhos instantâneos para pastas do Windows (*Músicas*, *Downloads*, *Área de Trabalho*) e seletor nativo para qualquer pasta do PC.
- **Acompanhamento em Tempo Real:** Barra de progresso dinâmica com percentual, contador de faixas e controle de cancelamento.

---

## 🚀 Como Usar

### 1. Iniciar o Aplicativo
- Dê dois cliques no atalho **SoundPro** na sua Área de Trabalho (ou execute `dist/SoundPro.exe`).
- O navegador padrão do computador abrirá automaticamente em `http://127.0.0.1:5000`.

### 2. Pesquisar ou Colar Link
- Digite o nome de uma música/artista (ex: `Coldplay Yellow`) ou cole o link de um vídeo ou playlist do YouTube.
- Clique em **Analisar** (ou pressione **Enter**).

### 3. Escolher o Formato e Baixar
- Escolha o formato desejado: **MP3 (Áudio)** ou **MP4 (Vídeo)**.
- Clique no botão de download da faixa individual ou em **Baixar Tudo** para baixar a playlist completa.
- Ao concluir, clique em **Abrir Pasta** para visualizar seus arquivos prontos para ouvir!

---

## 📁 Estrutura do Projeto

```text
├── app.py                     # Servidor local Flask e rotas de controle
├── logic.py                   # Motor de download (yt-dlp, FFmpeg, ID3 e capas)
├── templates/
│   ├── index.html             # Interface web estilo Spotify Desktop
│   └── icone.ico              # Ícone da aplicação
├── dist/
│   └── SoundPro.exe           # Executável portátil para Windows (FFmpeg embutido)
├── ffmpeg/                    # Binários do FFmpeg para conversão
├── SoundPro.spec              # Configuração de compilação do PyInstaller
└── requirements.txt           # Dependências Python (para desenvolvimento)
```

---

## ⚙️ Executando em Modo Desenvolvimento (Opcional)

Se você preferir executar diretamente pelo Python:

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicie o servidor:
   ```bash
   python app.py
   ```
3. O aplicativo abrirá no seu navegador em `http://127.0.0.1:5000`.
