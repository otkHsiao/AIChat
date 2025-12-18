import { useState, useEffect } from 'react'

/**
 * 自定义 Hook 用于监听媒体查询
 * @param query - CSS 媒体查询字符串
 * @returns 是否匹配媒体查询
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches
    }
    return false
  })

  useEffect(() => {
    if (typeof window === 'undefined') return

    const mediaQuery = window.matchMedia(query)
    
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    // 设置初始值
    setMatches(mediaQuery.matches)

    // 监听变化
    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [query])

  return matches
}

// 预定义的断点
export const breakpoints = {
  mobile: '(max-width: 480px)',
  tablet: '(max-width: 768px)',
  desktop: '(min-width: 769px)',
  largeDesktop: '(min-width: 1200px)',
}

/**
 * 判断是否为移动设备
 */
export function useIsMobile(): boolean {
  return useMediaQuery(breakpoints.mobile)
}

/**
 * 判断是否为平板或更小的设备
 */
export function useIsTablet(): boolean {
  return useMediaQuery(breakpoints.tablet)
}

/**
 * 判断是否为桌面设备
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(breakpoints.desktop)
}