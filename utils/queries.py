COMMIT_REFERENCES_PR = """
query ($owner: String!, $name: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $prNumber) {
      timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {
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
"""

COMMIT_REFERENCES_ISSUE = """
query ($owner: String!, $name: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $issueNumber) {
      timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {
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
"""

REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    createdAt
    issues(first:20, after:$after, states:CLOSED) {
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
                    message
                  }
                  author {
                    login
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
      }
    }
  }
}
"""