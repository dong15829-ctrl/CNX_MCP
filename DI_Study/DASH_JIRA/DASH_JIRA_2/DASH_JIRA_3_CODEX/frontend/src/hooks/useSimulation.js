import { useCallback, useEffect, useState } from 'react'
import {
  fetchSimulationState,
  resetSimulation,
  simulateNextBatch,
} from '../api/dashboard'

export function useSimulation(onAfterChange) {
  const [state, setState] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadState = useCallback(async () => {
    try {
      const data = await fetchSimulationState()
      setState(data)
    } catch (err) {
      setError(err.message || '시뮬레이션 상태를 불러오지 못했습니다')
    }
  }, [])

  useEffect(() => {
    loadState()
  }, [loadState])

  const runBatch = useCallback(
    async (batch = 1) => {
      setLoading(true)
      setError(null)
      try {
        const data = await simulateNextBatch(batch)
        setState(data)
        if (onAfterChange) {
          await onAfterChange()
        }
      } catch (err) {
        setError(err.message || '시뮬레이션 실행에 실패했습니다')
      } finally {
        setLoading(false)
      }
    },
    [onAfterChange],
  )

  const handleReset = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await resetSimulation()
      setState(data)
      if (onAfterChange) {
        await onAfterChange()
      }
    } catch (err) {
      setError(err.message || '시뮬레이션 초기화에 실패했습니다')
    } finally {
      setLoading(false)
    }
  }, [onAfterChange])

  return {
    state,
    loading,
    error,
    runBatch,
    reset: handleReset,
    reload: loadState,
  }
}
