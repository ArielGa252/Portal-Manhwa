# Portal Manhwa

Site estático para GitHub Pages com:

- Página inicial com busca
- Cards de manhwas
- Marcar como lido
- Capítulo atual salvo no navegador
- Marcar finalizado
- Página da obra
- Lista de capítulos
- Leitor próprio com imagens

## Arquivos principais

- `index.html`: estrutura do site
- `style.css`: visual do site
- `app.js`: funcionamento do site
- `manhwas.js`: banco de dados dos manhwas e capítulos

## Como editar os manhwas

Abra `manhwas.js` e adicione os dados assim:

```js
{
  id: 187,
  nome: "Nome do Manhwa",
  status: "COMPLETO",
  imagem: "https://link-da-capa.jpg",
  descricao: "Descrição da obra",
  capitulos: [
    {
      numero: 1,
      titulo: "Capítulo 1",
      imagens: [
        "https://link-da-pagina-1.jpg",
        "https://link-da-pagina-2.jpg"
      ]
    }
  ]
}
```

## Como ativar no GitHub Pages

Vá em:

Settings → Pages → Build and deployment → Deploy from a branch → `main` → `/root`

Depois o site deve abrir em:

`https://ArielGa252.github.io/Portal-Manhwa/`
