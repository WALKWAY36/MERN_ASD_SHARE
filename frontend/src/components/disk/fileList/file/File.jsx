import React, { useState, useEffect, useCallback } from 'react';
import './file.css';
import dirLogo from '../../../../assets/img/dir.svg';
import fileLogo from '../../../../assets/img/file.svg';
import { useSelector, useDispatch } from 'react-redux';
import { pushToStack, setCurrentDir } from '../../../../reducers/fileReducer';
import { deleteFile, downloadFile } from '../../../../actions/file';
import { startAnalysis, getAnalysisStatus, getFileAnalytics } from '../../../../actions/ml';
import sizeFormat from '../../../../utils/sizeFormat';
import { auth } from '../../../../actions/user';
import { VideoAnalyticsModal } from "./VideoAnalyticsModal";
import { VideoPlayerModal } from "./VideoPlayerModal";

const File = ({ file }) => {
  const dispatch = useDispatch();
  const userId = useSelector((state) => state.user.currentUser.id);
  const currentDir = useSelector((state) => state.files.currentDir);
  const fileView = useSelector((state) => state.files.view);
  const token = useSelector((state) => state.user.token);

  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStatus, setAnalysisStatus] = useState('idle');
  const [analysisError, setAnalysisError] = useState(null);
  const [hasAnalysis, setHasAnalysis] = useState(false);

  // Проверяем расширение файла
  const fileName = file.name || '';
  const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
  const isVideo = ['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(fileExt);

  console.log('File:', file.name, 'isVideo:', isVideo, 'type:', file.type, 'analysisStatus:', file.hasAnalysis);

  // Проверяем статус анализа при монтировании
  useEffect(() => {
    if (isVideo && file.hasAnalysis) {
      console.log('Setting completed for:', file.name);
      setHasAnalysis(true);
      setAnalysisStatus('completed');
    }
  }, [file, isVideo]);

  // Поллинг статуса анализа
  useEffect(() => {
    let interval;
    
    if (isAnalyzing) {
      interval = setInterval(async () => {
        try {
          const status = await dispatch(getAnalysisStatus());
          
          if (status) {
            setAnalysisProgress(status.progress || 0);
            
            if (!status.is_analyzing) {
              clearInterval(interval);
              setIsAnalyzing(false);
              
              if (status.result) {
                setAnalysisStatus('completed');
                setHasAnalysis(true);
                setAnalyticsData(status.result);
              } else if (status.error) {
                setAnalysisStatus('failed');
                setAnalysisError(status.error);
              }
            }
          }
        } catch (error) {
          console.error('Status poll error:', error);
        }
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAnalyzing, dispatch]);

  const startAnalysisHandler = async (e) => {
    e.stopPropagation();
    
    try {
      setIsAnalyzing(true);
      setAnalysisStatus('analyzing');
      setAnalysisProgress(0);
      setAnalysisError(null);
      
      const result = await dispatch(startAnalysis(file._id));
      
      if (result) {
        setAnalysisStatus('completed');
        setHasAnalysis(true);
        setAnalyticsData(result);
        setAnalysisProgress(100);
        setIsAnalyzing(false);
      }
      
    } catch (error) {
      console.error('Analysis error:', error);
      
      if (error.message?.includes('уже анализируется') || error.status === 409) {
        setAnalysisError('Другое видео анализируется, ожидайте...');
        // Не сбрасываем isAnalyzing, продолжаем поллинг
      } else {
        setAnalysisStatus('failed');
        setAnalysisError(error.message || 'Ошибка анализа');
        setIsAnalyzing(false);
      }
    }
  };

  const openAnalyticsHandler = async (e) => {
    e.stopPropagation();
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await dispatch(getFileAnalytics(file._id));
      setAnalyticsData(response);
      setShowAnalytics(true);
      
    } catch (error) {
      console.error('Ошибка загрузки аналитики:', error);
      dispatch({
        type: 'SET_NOTIFICATION',
        payload: {
          type: 'error',
          message: 'Не удалось загрузить аналитику файла'
        }
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const watchVideoHandler = (e) => {
    e.stopPropagation();
    setShowPlayer(true);
  };

  function openDirHandler() {
    dispatch(auth());
    if (file.type === 'dir') {
      dispatch(pushToStack(currentDir));
      dispatch(setCurrentDir(file._id));
    }
  }

  function downloadClickHandler(e) {
    dispatch(auth());
    e.stopPropagation();
    downloadFile(file);
  }

  function deleteClickHandler(e) {
    dispatch(auth());
    e.stopPropagation();
    dispatch(deleteFile(file, userId));
  }

  // Кнопка анализа/аналитики
  const renderAnalysisButton = () => {
    if (!isVideo || file.type === 'dir') {
      console.log('Not rendering analysis button for:', file.name, 'isVideo:', isVideo, 'type:', file.type);
      return null;
    }
    
    if (analysisStatus === 'analyzing' || isAnalyzing) {
      console.log("Идёт анализ...")
      return (
        <button className="file__btn file__analyzing" disabled>
          <span className="spinner-border spinner-border-sm me-1" />
          <span>{analysisProgress > 0 ? `${analysisProgress}%` : '...'}</span>
        </button>
      );
    }
    
    if (analysisStatus === 'completed' || hasAnalysis || file.analysisStatus === 'completed') {
      return (
        <button onClick={openAnalyticsHandler} className="file__btn  file__open">
          аналитика
        </button>
      );
    }
    
    if (analysisStatus === 'failed') {
      return (
        <button onClick={startAnalysisHandler} className="file__btn file__retry" title={analysisError}>
          повторить
        </button>
      );
    }
    
    // По умолчанию — кнопка "анализировать"
    return (
      <button onClick={startAnalysisHandler} className="file__btn file__open">
        анализировать
      </button>
    );
  };

  if (fileView === 'list') {
    return (
      <>
        <div className="file" onClick={() => openDirHandler(file)}>
          <img src={file.type === 'dir' ? dirLogo : fileLogo} alt="" className="file__img" />
          <div className="file__name">{fileName.slice(0, 20)}</div>
          <div className="file__date">{file?.date?.slice(0, 10)}</div>
          <div className="file__size">{sizeFormat(file.size)}</div>
          
          {file.type !== 'dir' && (
            <>
              {isVideo && (analysisStatus === 'completed' || hasAnalysis || file.analysisStatus === 'completed') && (
                <button onClick={watchVideoHandler} className="file__btn file__watch">
                  смотреть
                </button>
              )}
              
              {renderAnalysisButton()}
              
              <button onClick={downloadClickHandler} className="file__btn file__download">
                скачать
              </button>
            </>
          )}
          
          <button onClick={deleteClickHandler} className="file__btn file__delete">
            удалить
          </button>
          
          {analysisStatus === 'analyzing' && (
            <div className="file__progress-bar">
              <div className="file__progress-fill" style={{ width: `${analysisProgress}%` }} />
            </div>
          )}
        </div>
        
        {analysisError && analysisStatus === 'analyzing' && (
          <div className="file__analysis-notice">{analysisError}</div>
        )}
        
        {showAnalytics && analyticsData && (
          <VideoAnalyticsModal 
            fileData={analyticsData} 
            onClose={() => {
              setShowAnalytics(false);
              setAnalyticsData(null);
            }}
          />
        )}
        
        {showPlayer && (
          <VideoPlayerModal 
            file={file}
            token={token}
            userId={userId}
            onClose={() => setShowPlayer(false)}
          />
        )}

        {/* {analysisStatus === 'analyzing' && (
  <div className="file__progress-container">
    <div 
      className="file__progress-fill" 
      style={{ width: `${analysisProgress}%` }}
    />
          </div>
          
        )}
        {analysisStatus === 'analyzing' && (
  <span className="file__analysis-indicator">
    <span className="spinner-border spinner-border-sm" />
    <span className="file__progress-text">{analysisProgress}%</span>
  </span>
)} */}
      </>
    );
  }
  
  if (fileView === 'plate') {
    return (
      <div className="file-plate" onClick={() => openDirHandler(file)}>
        <img src={file.type === 'dir' ? dirLogo : fileLogo} alt="" className="file-plate__img" />
        <div className="file-plate__name">{fileName}</div>
        
        {analysisStatus === 'analyzing' && (
          <div className="file-plate__progress">
            <div className="progress" style={{ height: '4px' }}>
              <div className="progress-bar bg-info" style={{ width: `${analysisProgress}%` }} />
            </div>
            <small className="text-muted">{analysisProgress}%</small>
          </div>
        )}
        
        <div className="file-plate__btns">
          {file.type !== 'dir' && (
            <>
              {isVideo && (
                <button onClick={watchVideoHandler} className="file-plate__btn file-plate__watch">
                  смотреть
                </button>
              )}
              
              {renderAnalysisButton()}
              
              <button onClick={downloadClickHandler} className="file-plate__btn file-plate__download">
                скачать
              </button>
            </>
          )}
          
          <button onClick={deleteClickHandler} className="file-plate__btn file-plate__delete">
            удалить
          </button>
        </div>
      </div>
    );
  }
};

export default File;