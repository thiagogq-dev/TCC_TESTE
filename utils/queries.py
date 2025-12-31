REPO_CLOSED_ISSUES_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, states: CLOSED) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        createdAt
        closedAt
        url
      }
    }
  }
}
"""

REPO_PULL_REQUESTS_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 20, after: $after, states: MERGED) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        createdAt
        mergedAt
        url
        author {
          login
          url
        }
        closingIssuesReferences(first: 10) {
          nodes {
            number
            url
          }
        }
      }
    }
  }
}
"""

REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 20, after: $after, states: CLOSED) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        createdAt
        closedAt
        url
        author {
          login
          url
        }
        timelineItems(itemTypes: CLOSED_EVENT, last: 1) {
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
                  url
                  commits(last: 1) {
                    nodes {
                      commit {
                        oid
                      }
                    }
                  }
                  mergeCommit {
                    oid
                  }
                  author {
                    login
                  }
                }
                ... on Commit {
                  oid
                  committedDate
                  messageHeadline
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
      }
    }
  }
}
"""
