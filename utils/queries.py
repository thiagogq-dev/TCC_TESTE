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