import { makeStyles, tokens } from '@fluentui/react-components'
import { Outlet } from 'react-router-dom'

import { useAppSelector } from '../../store'
import Sidebar from '../Sidebar/Sidebar'
import Header from './Header'

const useStyles = makeStyles({
  root: {
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
  },
  main: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    overflow: 'hidden',
    backgroundColor: tokens.colorNeutralBackground2,
  },
  content: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
})

export default function AppLayout() {
  const classes = useStyles()
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen)

  return (
    <div className={classes.root}>
      {sidebarOpen && <Sidebar />}
      <main className={classes.main}>
        <Header />
        <div className={classes.content}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}