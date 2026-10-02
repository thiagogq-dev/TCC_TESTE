# Setup

1. Crie um ambiente virtual para instalar as dependências, e ative-o:
    
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2. Instalar as dependências
    ```bash
    pip install -r requirements.txt
    ```

3. Realize o clone dos seis repositórios do estudo

    ```bash
    # criar diretório dos repositórios
    mkdir repos_dir
    cd repos_dir
    ```
    
    ```bash
    git clone https://github.com/apache/pulsar.git
    git clone https://github.com/elastic/elasticsearch.git
    git clone https://github.com/JabRef/jabref.git
    git clone https://github.com/junit-team/junit-framework.git
    git clone https://github.com/keycloak/keycloak.git
    git clone https://github.com/spring-projects/spring-boot.git
    ```

4.  Copie o arquivo .env.example para um `.env` e crie os tokens de API necessários para fazer as requisições. 
Para o caso do `START_CURSOR`, deixe vazio para a primeira requisição

    ```env
    START_CURSOR=

    API_TOKEN_1=ghp_...
    API_TOKEN_2=ghp_...
    API_TOKEN_3=ghp_...
    ```

5. Realizar a coleta de dados

    ```bash
    python3 collect_issues.py
    ```

6. Usar o [modelo BERT](https://github.com/s2e-lab/BERT-Based-GitHub-Issue-Classification) usado para classificar as issues em issues de defeito ou não:
    - Nesse passo, ao rodar o software citado, é importante que o arquivo json que será passado como entrada para classificar seja modificado ao obter a classificação, para que a classificação atribuída seja adicionada na chave `predicted_class` do json, ficando da seguinte forma:

    ```json
    {
        "repo_name":"elasticsearch",
        "issue_number":2,
        "issue_title":"Discovery: Support local (JVM level) discovery",
        "issue_body":"Allow to have a JVM (well, actually class loader) level discovery for simple testing \/ embedding of a single node (which, potentially exists with other nodes in the same class loader).\n\nEnable it using:\n\n```\ndiscovery:\n    type: local\n```\n\nOr using:\n\n```\nnode:\n    local: true\n```\n\n(which will also enable other modules to be local, such as the transport - once we have that...)\n",
        "issue_url":"https:\/\/github.com\/elastic\/elasticsearch\/issues\/2",
        "assignees":[

        ],
        "labels":[
            ">feature",
            "v0.05.0"
        ],
        "issue_closed_at":"2010-02-10T22:12:58.000Z",
        "fix_commit_hash":"55a7227f67c308f0141e384e9553e759995e4189",
        "commit_type":"commit_ref_issue_no_event",
        "commit_message":"ESQL: external multi-file warm COUNT survives schema-TTL expiry and many-stripe cache pressure (#153085) (#153216)\n\n* ESQL: warm short-circuit...",
        "closer_url":null,
        "earliest_issue_date":"2010-02-10T22:10:55Z",
        "predicted_class":"enhancement"
    },
    ```

7. Separar as issues de defeito das de não defeito

    ```bash
    python3 split_bug_nobug.py
    ```

8. Execute o SZZ para o arquivo desejado:

    ```bash
    cd pyszz_v2
    bash ./run_docker.sh <arquivo_entrada> ./conf/asserts_article.yml ../repos_dir/
    ````

utf9. Mover arquivo gerado na pasta out/ do pyszz para a pasta de destino

    ```bash
    mkdir -p ../dataset/3-szz
    cp ./out/<nome_arquivop> ../dataset/3-szz/
    ```

10. Verificar se algum BIC retornado é um *merge commit* para atualizar os BIC
    
    ```bash
    python3 check_for_merge.py
    ```

11. Separar lista dos commtis de correção em com BIC e sem BIC retornado
    
    ```bash
    python3 split_bic_no_bic.py
    ```

12. Juntar a lista de commits relacionados a issues de não bugs e commits que não retornaram BIC

    ```bash
    python3 merge_no_bic_no_bug.py
    ```

13. Gerar lista de pares BIC->FIX e gerar lista de apenas commits com BIC

    ```bash
    python3 generate_fix_lists.py
    ```

14. Coletar dados de métricas e uso de asserts
    
    ```bash
    python3 mine_commit_data.py
    ```

15. Executar scripts de análise

    ```bash
    bash run_analyses.sh
    ````

# IMPORTANTE 

Para todos os scripts, as pastas de entrada e saída estão configuradas para utilizar os diretórios originais do projeto (./dataset e ./results). Essa configuração ocorre diretamente no código (seja em Python ou shell script). Caso os arquivos a serem processados ou salvos precisem ficar em um caminho diferente, será necessário alterar as variáveis nos scripts.