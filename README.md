# Hunter 🎯

Descobre quais skills o LinkedIn mais pede para uma carreira (ex.: *Engenheiro de dados júnior*)
e mede o quanto o seu perfil está aderente a esse mercado.

## Como rodar

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

## Fluxo

1. **Mercado**: informe cargo, localidade, nível e quantidade de vagas. A localidade aceita
   várias opções combinadas: `Brasil`, regiões (`Sudeste`), estados (`ES` ou `Espírito Santo`),
   cidades (`Vitória, ES`) ou qualquer lugar que o LinkedIn conheça (`Lisboa`). Também dá para
   incluir vagas remotas de todo o Brasil. Depois da busca, filtre por nível, região, estado e modalidade.
   O app lê as vagas públicas do LinkedIn e calcula **% das vagas que citam cada skill**.
   Use o filtro “nível pelo título”, porque o filtro de nível do LinkedIn deixa passar vagas de outros níveis.
2. **Palavras-chave**: títulos de cargo mais usados (com sugestão de título para o seu perfil),
   termos de 1 a 3 palavras mais frequentes nas descrições, quais deles faltam no seu perfil
   e trechos reais das vagas mostrando como cada termo é usado.
3. **Meu perfil**: envie o ZIP de dados do LinkedIn (*Configurações → Privacidade de dados →
   Baixe seus dados*), o PDF do perfil (*Mais → Salvar como PDF*) e/ou texto livre.
   Revise a lista de skills detectadas.
4. **Aderência**:
   - **Aderência ao mercado**: soma da demanda das skills que você tem ÷ demanda total das top N skills.
   - **Cobertura**: quantas das top N skills você tem.
   - Lista do que estudar primeiro, seus diferenciais e as vagas com maior match.

## Estrutura

| Arquivo | O que faz |
|---|---|
| `hunter/taxonomy.py` | Catálogo de skills e apelidos (PT/EN). Para rastrear uma skill nova, adicione uma linha. |
| `hunter/linkedin_jobs.py` | Coleta as vagas pelos endpoints públicos `jobs-guest` (sem login), com cache em `.cache/jobs`. |
| `hunter/profile.py` | Lê o ZIP do export, o PDF e o texto livre. |
| `hunter/keywords.py` | Palavras-chave, títulos de cargo e sugestão de título. |
| `hunter/locations.py` | Converte cidade/estado/região em localidades do LinkedIn; detecta estado e modalidade das vagas. |
| `hunter/analysis.py` | Ranking, aderência e match por vaga. |
| `app.py` | Interface em Streamlit. |

## Avisos

- O LinkedIn não oferece API pública de vagas. A coleta automatizada vai contra os Termos de Uso
  da plataforma. Use para fins pessoais e com volume baixo (o app já faz pausas e cache).
  O endpoint pode mudar ou passar a bloquear requisições (HTTP 429/999).
- A extração usa um dicionário de skills: é determinística e gratuita, mas só encontra o que está no catálogo.
