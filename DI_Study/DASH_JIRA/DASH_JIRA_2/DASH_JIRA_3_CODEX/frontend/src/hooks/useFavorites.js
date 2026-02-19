import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'jira_favorite_issues'

const readStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    console.warn('즐겨찾기 복원 실패', error)
    return []
  }
}

export function useFavorites() {
  const [favorites, setFavorites] = useState(() => readStorage())

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites))
    } catch (error) {
      console.warn('즐겨찾기 저장 실패', error)
    }
  }, [favorites])

  const toggleFavorite = useCallback((issueKey) => {
    setFavorites((prev) => {
      if (prev.includes(issueKey)) {
        return prev.filter((key) => key !== issueKey)
      }
      return [...prev, issueKey]
    })
  }, [])

  const clearFavorites = useCallback(() => setFavorites([]), [])

  const isFavorite = useCallback(
    (issueKey) => favorites.includes(issueKey),
    [favorites],
  )

  return {
    favorites,
    toggleFavorite,
    isFavorite,
    clearFavorites,
  }
}
