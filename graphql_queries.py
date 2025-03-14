VALIDATE_STEAM_ID_QUERY = """
query ($steamId: Long!) {
  player(steamAccountId: $steamId) {
    steamAccount {
      id
    }
  }
}
"""

PROFILE_QUERY = """
query ($steamId: Long!) {
  player(steamAccountId: $steamId) {
    steamAccount {
      name
      seasonRank
      avatar
      lastMatchDateTime
    }
    matchCount
    winCount
    behaviorScore
  }
}
"""

MATCH_HISTORY_QUERY = """
query ($steamId: Long!, $take: Int!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: $take}) {
      id
      didRadiantWin
      durationSeconds
      startDateTime
      players(steamAccountId: $steamId) {
        hero {
          displayName
        }
        kills
        deaths
        assists
        isVictory
      }
    }
  }
}
"""

LAST_MATCH_QUERY = """
query ($steamId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: 1}) {
      id
      durationSeconds
      startDateTime
      radiantKills
      direKills
      players(steamAccountId: $steamId) {
        hero {
          id
          displayName
          shortName
        }
        imp
        level
        numLastHits
        numDenies
        networth
        kills
        deaths
        assists
        isVictory
        goldPerMinute
        experiencePerMinute
        heroDamage
        item0Id
        item1Id
        item2Id
        item3Id
        item4Id
        item5Id
        backpack0Id
        backpack1Id
        backpack2Id
      }
    }
  }
  heroStats {
    stats {
      kills
      deaths
      assists
      networth
      xp
      time
    }
  }
}
"""

ITEMS = """
query {
  constants {
		items {
      id
      displayName
    }
  }
}
"""

HERO = """
query {
  constants {
    heroes {
      id
      shortName
      displayName
      roles {
        roleId
      }
    }
  }
}
"""

MATCH_ID_QUERY = """
query ($steamId: Long!, $matchId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: {matchIds: [$matchId]}) {
      id
      durationSeconds
      startDateTime
      radiantKills
      direKills
      players(steamAccountId: $steamId) {
        hero {
          id
          displayName
          shortName
        }
        imp
        level
        numLastHits
        numDenies
        networth
        kills
        deaths
        assists
        isVictory
        goldPerMinute
        experiencePerMinute
        heroDamage
        item0Id
        item1Id
        item2Id
        item3Id
        item4Id
        item5Id
        backpack0Id
        backpack1Id
        backpack2Id
      }
    }
  }
  heroStats {
    stats {
      kills
      deaths
      assists
      networth
      xp
      time
    }
  }
}
"""

META_QUERY = """
query {
 heroStats {
    winMonth (take: 1){
      heroId
      winCount
      matchCount
    }
  }
}
"""

TOP_HEROES = """
query ($steamId: Long!, $take: Int!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: $take}) {
      players(steamAccountId: $steamId) {
        hero {
          id
        }
        kills
        deaths
        assists
        isVictory
        goldPerMinute
        experiencePerMinute
        networth
      }
    }
  }
  heroStats {
    stats {
      kills
      deaths
      assists
      networth
      xp
      time
    }
  }
}
"""
