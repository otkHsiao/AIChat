import { useState, useRef, useEffect } from 'react'
import { makeStyles, tokens, Skeleton, SkeletonItem } from '@fluentui/react-components'

const useStyles = makeStyles({
  container: {
    position: 'relative',
    display: 'inline-block',
    overflow: 'hidden',
    borderRadius: tokens.borderRadiusSmall,
  },
  image: {
    display: 'block',
    maxWidth: '100%',
    height: 'auto',
    transition: 'opacity 0.3s ease-in-out',
  },
  imageLoading: {
    opacity: 0,
  },
  imageLoaded: {
    opacity: 1,
  },
  skeleton: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
  },
  error: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground3,
    fontSize: '12px',
    padding: tokens.spacingHorizontalM,
  },
})

interface LazyImageProps {
  src: string
  alt: string
  className?: string
  width?: number | string
  height?: number | string
  placeholder?: React.ReactNode
  onLoad?: () => void
  onError?: () => void
}

export function LazyImage({
  src,
  alt,
  className,
  width,
  height,
  placeholder,
  onLoad,
  onError,
}: LazyImageProps) {
  const classes = useStyles()
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Intersection Observer for lazy loading
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01,
      }
    )

    if (containerRef.current) {
      observer.observe(containerRef.current)
    }

    return () => observer.disconnect()
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  const containerStyle: React.CSSProperties = {
    width: width || 'auto',
    height: height || 'auto',
    minHeight: isLoaded ? 'auto' : height || '100px',
    minWidth: isLoaded ? 'auto' : width || '100px',
  }

  if (hasError) {
    return (
      <div
        ref={containerRef}
        className={`${classes.container} ${classes.error} ${className || ''}`}
        style={containerStyle}
      >
        图片加载失败
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`${classes.container} ${className || ''}`}
      style={containerStyle}
    >
      {/* Skeleton placeholder */}
      {!isLoaded && (
        <div className={classes.skeleton}>
          {placeholder || (
            <Skeleton>
              <SkeletonItem
                style={{
                  width: '100%',
                  height: '100%',
                  minHeight: typeof height === 'number' ? height : 100,
                }}
              />
            </Skeleton>
          )}
        </div>
      )}

      {/* Actual image - only load src when in view */}
      {isInView && (
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          className={`${classes.image} ${
            isLoaded ? classes.imageLoaded : classes.imageLoading
          }`}
          onLoad={handleLoad}
          onError={handleError}
          style={{
            maxWidth: width || '100%',
            maxHeight: height || 'auto',
          }}
        />
      )}
    </div>
  )
}

export default LazyImage