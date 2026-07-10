""""
Query para coletar issues fechadas e eventos de fechamento de um repositório no GitHub.
Esta query retorna informações detalhadas sobre issues fechadas, incluindo:
- Número da issue
- Título e corpo da issue
- URL da issue
- Assignees e labels associados à issue
- Data de criação e fechamento da issue
- Eventos de fechamento (ClosedEvent) e commits referenciados (ReferencedEvent)
A query é paginada, permitindo a coleta de todas as issues fechadas em um repositório, mesmo que haja mais de 100 issues. Para isso, é necessário fornecer o cursor `after` na variável de entrada da query para buscar a próxima página de resultados.
Args:
    owner (str): Nome do proprietário do repositório.
    name (str): Nome do repositório.
    after (str, opcional): Cursor para paginação. Se fornecido, a query retornará issues fechadas após o cursor especificado.
Returns:
    dict: Dicionário contendo informações sobre as issues fechadas e seus eventos de fechamento.
"""
REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    createdAt
    issues(first:100, after:$after, states:CLOSED) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        url
        assignees(first: 10) {
          nodes {
            login
            url
          }
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        createdAt
        closedAt
        closedEvents: timelineItems(itemTypes: CLOSED_EVENT, last: 1) {
          nodes {
            ... on ClosedEvent {
              createdAt
              closer {
                __typename
                ... on PullRequest {
                  number
                  url
                  title
                  createdAt
                  mergedAt
                  commits(last: 1) {
                    nodes {
                      commit {
                        oid
                      }
                    }
                  }
                  mergeCommit {
                    oid
                    message
                  }
                  author {
                    login
                  }
                  referencedCommit: timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {
                    nodes {
                      ... on ReferencedEvent {
                        commit {
                          oid
                          message
                        }
                      }
                    }
                  }
                }
                ... on Commit {
                  oid
                  message
                  committedDate
                  url
                  author {
                    user {
                      login
                      url
                    }
                  }
                }
              }
            }
          }
        }
        referencedEvents: timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {
          nodes {
            ... on ReferencedEvent {
              commit {
                oid
                message
              }
            }
          }
        }
      }
    }
  }
}
"""