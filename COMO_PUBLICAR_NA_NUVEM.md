# Como Publicar o SoundPro Online (100% Grátis na Nuvem)

Com este guia, você terá um link público permanente (ex: `https://seu-soundpro.onrender.com`) para usar o SoundPro no seu celular de qualquer lugar pelo 4G/Wi-Fi, **sem precisar do computador ligado**.

---

## Passo 1: Subir o código para o seu GitHub

1. Se ainda não tiver o Git configurado no projeto, abra o PowerShell nesta pasta e execute:
   ```bash
   git init
   git add .
   git commit -m "SoundPro Cloud"
   ```

2. Crie um novo repositório vazio no seu [GitHub](https://github.com/new) (pode ser Público ou Privado, com o nome `soundpro`).

3. Vincule e envie o código executando (substitua pelo link do seu repositório):
   ```bash
   git remote add origin https://github.com/SEU_USUARIO/soundpro.git
   git branch -M main
   git push -u origin main
   ```

---

## Passo 2: Publicar no Render.com (Grátis)

1. Acesse **[Render.com](https://render.com)** e crie uma conta (pode clicar em **Sign in with GitHub** para conectar direto).
2. No painel do Render, clique no botão **New +** no topo direito e escolha **Web Service**.
3. Escolha **Build and deploy from a Git repository** e selecione o repositório `soundpro` que você acabou de subir.
4. Preencha as configurações (já estão pré-configuradas no projeto):
   - **Name:** `soundpro` (ou o nome que preferir)
   - **Language:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Instance Type:** `Free` (Grátis)
5. Clique em **Create Web Service**.
6. Aguarde cerca de 1 a 2 minutos enquanto o Render instala os pacotes e inicializa.

---

## Passo 3: Abrir e Instalar no Celular

1. Quando o Render concluir, ele exibirá o link da sua aplicação no topo, por exemplo:
   `https://soundpro-xxxx.onrender.com`
2. Abra esse link no navegador do seu smartphone (Google Chrome no Android ou Safari no iPhone).
3. **Instale como aplicativo**:
   - **No Android (Chrome):** Toque nos **3 pontinhos** no canto superior direito e selecione **"Adicionar à tela inicial"** ou **"Instalar aplicativo"**.
   - **No iPhone (Safari):** Toque no botão de **Compartilhar** (quadrado com seta para cima) e escolha **"Adicionar à Tela de Início"**.
4. Pronto! O SoundPro estará na sua tela inicial como um aplicativo nativo. Todas as músicas pesquisadas e baixadas irão direto para o armazenamento do seu smartphone!
