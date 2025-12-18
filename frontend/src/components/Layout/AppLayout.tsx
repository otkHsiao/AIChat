import { useEffect } from 'react'
import { makeStyles, tokens, mergeClasses } from '@fluentui/react-components'
import { Outlet } from 'react-router-dom'

import { useAppSelector, useAppDispatch } from '../../store'
import { setMobileView } from '../../features/ui/uiSlice'
import Sidebar from '../Sidebar/Sidebar'
import Header from './Header'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
    position: 'relative',
  },
  main: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    overflow: 'hidden',
    backgroundColor: tokens.colorNeutralBackground2,
    minWidth: 0, // 允许 flex 收缩
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  // 移动端侧边栏遮罩层
  overlay: {
    display: 'none',
  },
  overlayVisible: {
    display: 'block',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 99,
  },
  // 移动端侧边栏样式
  sidebarMobile: {
    position: 'fixed',
    top: 0,
    left: 0,
    bottom: 0,
    zIndex: 100,
    transform: 'translateX(-100%)',
    transition: 'transform 0.3s ease-in-out',
  },
  sidebarMobileOpen: {
    transform: 'translateX(0)',
  },
})

export default function AppLayout() {
  const classes = useStyles()
  const dispatch = useAppDispatch()
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen)
  const isMobileView = useAppSelector((state) => state.ui.isMobileView)

  // 监听窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth <= 768
      dispatch(setMobileView(isMobile))
    }

    // 初始化
    handleResize()

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [dispatch])

  // 点击遮罩层关闭侧边栏
  const handleOverlayClick = () => {
    if (isMobileView && sidebarOpen) {
      dispatch({ type: 'ui/setSidebarOpen', payload: false })
    }
  }

  return (
    <div className={classes.root}>
      {/* 移动端遮罩层 */}
      {isMobileView && (
        <div
          className={mergeClasses(
            classes.overlay,
            sidebarOpen && classes.overlayVisible
          )}
          onClick={handleOverlayClick}
        />
      )}

      {/* 侧边栏 */}
      {isMobileView ? (
        // 移动端：固定定位，带动画
        sidebarOpen && (
          <div className={mergeClasses(
            classes.sidebarMobile,
            sidebarOpen && classes.sidebarMobileOpen
          )}>
            <Sidebar />
          </div>
        )
      ) : (
        // 桌面端：正常布局
        sidebarOpen && <Sidebar />
      )}

      <main className={classes.main}>
        <Header />
        <div className={classes.content}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}