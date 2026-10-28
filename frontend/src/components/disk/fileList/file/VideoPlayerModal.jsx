import React, { useEffect, useRef, useState } from 'react';
import './VideoPlayerModal.css';
import { API_URL } from '../../../../config';
export const VideoPlayerModal = ({ file,userId, token, onClose }) => {
  const [videoUrl, setVideoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);

  useEffect(() => {
    // Создаем URL для стриминга
    const streamUrl = `${API_URL}/api/video/stream/${file._id}/${userId}`;
    console.log("streamUrl: ", streamUrl)
    setVideoUrl(streamUrl);
    setIsLoading(false);

    // Обработчик закрытия по ESC
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    
    return () => {
      window.removeEventListener('keydown', handleEsc);
      // Останавливаем видео при закрытии
      if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.src = '';
      }
    };
  }, [file._id, onClose]);

  // Обработчик клика по фону
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="video-modal-overlay" onClick={handleBackdropClick}>
      <div className="video-modal-container">
        <div className="video-modal-header">
          <h3 className="video-modal-title">{file.name}</h3>
          <button className="video-modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="video-modal-body">
          {isLoading ? (
            <div className="video-loading">
              <div className="spinner"></div>
              <p>Загрузка видео...</p>
            </div>
          ) : error ? (
            <div className="video-error">
              <p>Ошибка загрузки видео: {error}</p>
              <button onClick={() => window.location.reload()}>Повторить</button>
            </div>
          ) : (
            <video
              ref={videoRef}
              className="video-player"
              controls
              autoPlay
              preload="metadata"
              controlsList="nodownload"
            >
              <source src={videoUrl} type="video/mp4" />
              <source src={videoUrl} type="video/webm" />
              <source src={videoUrl} type="video/quicktime" />
              Ваш браузер не поддерживает видео тег.
            </video>
          )}
        </div>
        
        <div className="video-modal-footer">
          <div className="video-info">
            <span>Размер: {(file.size / (1024 * 1024)).toFixed(2)} MB</span>
            <span>Тип: {file.type || 'video'}</span>
          </div>
          <button className="video-download-btn" onClick={() => {
            window.open(videoUrl, '_blank');
          }}>
            Скачать видео
          </button>
        </div>
      </div>
    </div>
  );
};