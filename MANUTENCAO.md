# Manutenção do perfil

O `README.md` e as imagens em `assets/` são gerados. Não edite esses arquivos à mão:
mude o `perfil.json` (ou os repositórios) e deixe o gerador refazer tudo.

## Quando atualiza

- Todo dia às 06:17 (horário de Brasília), pela action `atualizar perfil`.
- Na hora, sempre que `perfil.json` ou `scripts/` mudarem na branch `main`.
- Manualmente: aba **Actions** > `atualizar perfil` > **Run workflow**.

O GitHub pausa agendamentos em repositórios sem atividade por 60 dias. Se isso
acontecer, um aviso aparece na aba Actions; basta reativar ou rodar manualmente.

## Publicar um projeto novo

1. Crie o repositório como **público**.
2. Escreva a descrição do repositório (é ela que aparece na tabela).
3. Adicione tópicos. O primeiro tópico que bater com uma área do `perfil.json`
   decide onde o projeto aparece:

   | área | tópicos |
   |:--|:--|
   | Aplicações web e ferramentas | `web` `php` `javascript` `ferramentas` |
   | Robótica e simulação | `robotica` `robocup` `simulacao` `cpp` |
   | Automação e dados | `automacao` `python` `dados` `scripts` |
   | Estudos e experimentos | `estudo` `ifes` `experimento` |

   Sem tópico conhecido, o projeto vai para "Outros projetos".
   Pelo terminal: `gh repo edit beraymundo/<repo> --description "..." --add-topic web`

4. Pronto. No dia seguinte (ou rodando a action) ele aparece no perfil, no
   terminal do topo e na barra de linguagens.

## O que dá para ajustar no perfil.json

| campo | efeito |
|:--|:--|
| `titulo`, `resumo`, `local` | texto do terminal no topo |
| `sobre` | parágrafos da seção sobre |
| `capacidades` | tabela "o que posso fazer" (`[rótulo, texto]`) |
| `ferramentas` | lista em `~/stack`, além das linguagens medidas nos repositórios |
| `areas`, `area_padrao` | grupos da seção de projetos e os tópicos que levam a cada um |
| `repos.<nome>` | nome amigável, `descricao`, `stack` (lista) ou `area` fixa para um repositório; para repositórios de organização use `dono/nome` |
| `repos_externos` | repositórios públicos de organizações em que você participa (`"dono/nome"`); entram como os seus |
| `destaques` | repositórios que vêm primeiro dentro da sua área |
| `ocultar` | repositórios públicos que não devem aparecer |
| `incluir_forks` | forks que devem aparecer (por padrão forks ficam de fora) |
| `fora_do_github` | projetos privados ou sem repositório (`nome`, `stack`, `descricao`, `url` opcional) |
| `nota_projetos` | frase abaixo de `~/projetos`; apague quando não fizer mais sentido |
| `contato` | `email`, `linkedin`, `site`; a seção só aparece se algum estiver preenchido |

Repositórios privados e arquivados nunca aparecem automaticamente.

## Rodar localmente

```
gh auth token      # copie o token
set GITHUB_TOKEN=<token>      (cmd)  |  $env:GITHUB_TOKEN = (gh auth token)  (PowerShell)
python scripts/atualizar.py
```

Só usa a biblioteca padrão do Python 3.
