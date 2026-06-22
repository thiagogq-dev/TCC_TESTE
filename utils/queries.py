COMMIT_REFERENCES_PR = """
query ($owner: String!, $name: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $prNumber) {
      timelineItems(itemTypes: REFERENCED_EVENT, last: 1) {
        nodes {
          ... on ReferencedEvent {
            commit {
              oid
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
            }
          }
        }
      }
    }
  }
}
"""

REPO_CLOSED_ISSUES_AND_CLOSED_EVENTS_QUERY = """
query ($queryString: String!, $first: Int!, $after: String) {
  search(query: $queryString, type: ISSUE, first: $first, after: $after) {
    issueCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Issue {
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

REPO_CREATION_DATE_QUERY = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    createdAt
  }
}
"""