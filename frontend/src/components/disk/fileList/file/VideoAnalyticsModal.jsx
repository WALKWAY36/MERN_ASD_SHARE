// components/VideoAnalyticsModal.jsx
import './VideoAnalyticsModal.css';

const VideoAnalyticsModal = ({ fileData, onClose }) => {
  if (!fileData) return null;

    const { video_metadata, aggregated_features, preliminary_annotation, quality_metrics, } = fileData.analytics;
    const { ml_insights, mlPrediction} = fileData.mlPrediction
    console.log(fileData)
  const mlData = ml_insights?.prediction || mlPrediction || fileData.mlPrediction;
  console.log(mlData)
  const combinedRisk = ml_insights?.combined_risk_score;
  const finalAssessment = ml_insights?.final_assessment;
  const isConsistent = preliminary_annotation && mlData && mlData.available !== false && 
  ((preliminary_annotation.risk_score <= 2 && mlData.prediction === "Норма") ||
   (preliminary_annotation.risk_score > 2 && mlData.prediction !== "Норма"));

  const translateKey = (key) => {
    const translations = {
      'bilateral_asymmetry': 'асимметрия',
     'mlPrediction': 'Предсказание ML модели',
      'prediction': 'Предсказание',
      'prediction_label': 'Метка предсказания',
      'confidence': 'Уверенность модели',
      'probability_normal': 'Вероятность нормы',
      'probability_asd': 'Вероятность РАС',
      'video_id': 'ID видео',
      'duration_sec': 'Длительность (сек)',
      'fps': 'Кадров в секунду',
      'resolution': 'Разрешение',
      'total_frames': 'Всего кадров',
      'recording_date': 'Дата записи',
      'total_abrupt_movements': 'Всего резких движений',
      'movements_per_minute': 'Движений в минуту',
      'symmetry_metrics': 'Метрики симметрии',
      'frequency_features': 'Частотные характеристики',
      'amplitude_features': 'Амплитудные характеристики',
      'movement_frequency': 'Частота движений',
      'preliminary_label': 'Предварительная метка',
      'risk_score': 'Оценка риска',
      'risk_factors': 'Факторы риска',
      'detection_rate': 'Коэффициент обнаружения',
      'avg_keypoint_confidence': 'Средняя уверенность ключевых точек',
      'missing_frames': 'Пропущенные кадры',
      'sampling_rate_hz': 'Частота дискретизации (Гц)',
      'total_samples': 'Всего образцов',
      'dominant_frequency_hz': 'Доминирующая частота (Гц)',
      'frequency_range_hz': 'Диапазон частот (Гц)',
      'mean_speed': 'Средняя скорость',
      'std_speed': 'Стандартное отклонение скорости',
      'max_speed': 'Максимальная скорость',
      'speed_variance': 'Дисперсия скорости',
      'левое_запястье': 'Левое запястье',
      'правое_запястье': 'Правое запястье',
      'левое_колено': 'Левое колено',
      'правое_колено': 'Правое колено',
      'левая_лодыжка': 'Левая лодыжка',
      'правая_лодыжка': 'Правая лодыжка',
      'левое_запястье_vs_правое_запястье': 'Левое vs правое запястье',
      'левое_колено_vs_правое_колено': 'Левое vs правое колено',
      'левая_лодыжка_vs_правая_лодыжка': 'Левая vs правая лодыжка',
      'high_frequency': 'Высокая частота',
      'high_variability': 'Высокая вариативность'
    };
    return translations[key] || key;
  };

  const formatProbability = (prob) => {
    if (prob === undefined || prob === null) return '—';
    return `${(prob * 100).toFixed(2)}%`;
  };


  const getMLRiskColor = (prediction, confidence) => {
    if (!prediction) return 'neutral';
    
    if (prediction === "Норма" || prediction === "Нормальный") {
      if (confidence > 0.9) return 'low-risk';
      if (confidence > 0.7) return 'medium-low-risk';
      return 'medium-risk';
    } else {
      if (confidence > 0.9) return 'high-risk';
      if (confidence > 0.7) return 'medium-high-risk';
      return 'medium-risk';
    }
  };

 const getFinalRecommendation = (analytics, mlData) => {
  if (!mlData || mlData.available === false) {
    return analytics?.risk_score <= 2 
      ? 'Низкий риск. Рекомендуется наблюдение.'
      : 'Рекомендуется консультация специалиста.';
  }

  if (mlData.prediction === "Норма") {
    if (mlData.confidence > 0.9) {
      return 'Низкий риск. Вероятность РАС минимальна.';
    } else {
      return 'Умеренный риск. Рекомендуется наблюдение.';
    }
  } else {
    if (mlData.confidence > 0.9) {
      return 'Высокий риск РАС. Требуется консультация специалиста.';
    } else {
      return 'Потенциальный риск РАС. Рекомендуется дополнительное обследование.';
    }
  }
};

// Заглушки для функций кнопок (реализуйте позже)
const downloadReport = (data) => {
  console.log('Download report:', data);
  // Реализуйте скачивание отчета
};

const shareResults = (data) => {
  console.log('Share results:', data);
  // Реализуйте шеринг результатов
};


  const formatValue = (key, value) => {
    if (Array.isArray(value)) {
      return value.join(' × ');
    }
    if (typeof value === 'number') {
      if (key.includes('frequency') || key.includes('speed')) {
        return value.toFixed(2);
      }
      if (key.includes('date')) {
        return new Date(value).toLocaleString('ru-RU');
      }
      return value.toFixed(3);
    }
    return value;
  };

  const getRiskColor = (score) => {
    if (score <= 2) return 'low-risk';
    if (score <= 4) return 'medium-risk';
    return 'high-risk';
  };

  return (
  <div className="modal-overlay" onClick={onClose}>
    <div className="analytics-modal" onClick={e => e.stopPropagation()}>
      <button className="close-button" onClick={onClose}>×</button>
      
      <div className="analytics-header">
        <h2>Аналитика видео: {video_metadata?.video_id || 'Неизвестно'}</h2>
        <div className="recording-date">
          {video_metadata?.recording_date 
            ? new Date(video_metadata.recording_date).toLocaleDateString('ru-RU')
            : 'Дата не указана'}
        </div>
      </div>

      <div className="analytics-sections">
        {/* Секция с ML предсказанием - показываем первой */}
        {mlData &&  (
          <div className="analytics-section ml-prediction-section">
            <div className="section-header-with-icon">
              <h3>Анализ искусственного интеллекта</h3>
              {mlData.cached && (
                <span className="ml-cache-badge">Из кэша</span>
              )}
            </div>
            
            <div className={`ml-result-card ${getMLRiskColor(mlData.prediction, mlData.confidence)}`}>
              <div className="ml-result-main">
                <div className="ml-prediction">
                  <div className="ml-label">Диагностика:</div>
                  <div className="ml-value prediction-value">
                    {mlData.prediction === "Норма" 
                      ? <><strong>Нормальное развитие</strong></>
                      : <><strong>Признаки РАС</strong></>
                    }
                  </div>
                </div>
                
                <div className="ml-confidence">
                  <div className="ml-label">Уверенность модели:</div>
                  <div className="ml-value confidence-value">
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill" 
                        style={{ width: `${(mlData.confidence || 0) * 100}%` }}
                      />
                    </div>
                    <span className="confidence-percent">
                      {formatProbability(mlData.confidence)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Вероятностное распределение */}
              <div className="ml-probabilities">
                <div className="probability-row">
                  <span className="probability-label">Вероятность нормы:</span>
                  <span className="probability-value normal-prob">
                    {formatProbability(mlData.probability_normal)}
                  </span>
                </div>
                <div className="probability-row">
                  <span className="probability-label">Вероятность РАС:</span>
                  <span className="probability-value asd-prob">
                    {formatProbability(mlData.probability_asd)}
                  </span>
                </div>
              </div>

              {/* Интерпретация, если есть */}
              {mlData.interpretation && (
                <div className="ml-interpretation">
                  <div className="interpretation-label">Интерпретация:</div>
                  <div className="interpretation-content">
                    <div className="risk-level">
                      <strong>Уровень риска:</strong> {mlData.interpretation.risk_level}
                    </div>
                    <div className="recommendation">
                      <strong>Рекомендация:</strong> {mlData.interpretation.recommendation}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Сводка по времени */}
            {mlData.timestamp && (
              <div className="ml-timestamp">
                Анализ проведен: {new Date(mlData.timestamp).toLocaleString('ru-RU')}
              </div>
            )}
          </div>
        )}

        {/* Если ML модель недоступна */}
        {mlData && mlData.available === false && (
          <div className="analytics-section ml-unavailable-section">
            <h3>Искусственный интеллект</h3>
            <div className="warning-card">
              <div className="warning-icon">⚠️</div>
              <div className="warning-content">
                <h4>ML модель временно недоступна</h4>
                <p>Используются только данные стандартного анализа.</p>
                {mlData.fallback_prediction && (
                  <div className="fallback-info">
                    <strong>Приблизительная оценка:</strong> {mlData.fallback_prediction.note}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Секция сравнения аналитики и ML (если есть оба источника) */}
        {preliminary_annotation && mlData && mlData.available !== false && (
          <div className="analytics-section comparison-section">
            <h3>Сравнение методов анализа</h3>
            
            <div className="comparison-grid">
              <div className="comparison-card">
                <h4>Стандартный анализ</h4>
                <div className="comparison-content">
                  <div className="comparison-item">
                    <span>Оценка риска:</span>
                    <span className={`risk-badge risk-${preliminary_annotation.risk_score || 0}`}>
                      {preliminary_annotation.risk_score || '—'}/5
                    </span>
                  </div>
                  <div className="comparison-item">
                    <span>Факторы риска:</span>
                    <div className="factors-list">
                      {preliminary_annotation.risk_factors?.map(factor => (
                        <span key={factor} className="factor-tag">
                          {translateKey(factor)}
                        </span>
                      )) || '—'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="comparison-card">
                <h4>Искусственный интеллект</h4>
                <div className="comparison-content">
                  <div className="comparison-item">
                    <span>Предсказание:</span>
                    <span className={`prediction-badge ${mlData.prediction === "Норма" ? 'normal' : 'asd'}`}>
                      {mlData.prediction}
                    </span>
                  </div>
                  <div className="comparison-item">
                    <span>Уверенность:</span>
                    <span className="confidence-badge">
                      {formatProbability(mlData.confidence)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="comparison-card">
                <h4>Согласованность</h4>
                <div className="comparison-content">
                  <div className={`consistency-indicator ${isConsistent ? 'consistent' : 'inconsistent'}`}>
                    {isConsistent ? ' Согласовано' : ' Требуется проверка'}
                  </div>
                  {combinedRisk && (
                    <div className="comparison-item">
                      <span>Общая оценка риска:</span>
                      <span className="combined-risk">{combinedRisk}/5</span>
                    </div>
                  )}
                  {finalAssessment && (
                    <div className="comparison-item">
                      <span>Рекомендация:</span>
                      <span className="final-recommendation">
                        {finalAssessment.final_risk === 'requires_expert_review' 
                          ? 'Требуется экспертная оценка' 
                          : finalAssessment.final_risk}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Метаданные видео */}
        <div className="analytics-section">
          <h3>Метаданные видео</h3>
          <div className="metadata-grid">
            <div className="metadata-item">
              <span>Длительность:</span>
              <strong>{video_metadata.duration_sec.toFixed(2)} сек</strong>
            </div>
            <div className="metadata-item">
              <span>Разрешение:</span>
              <strong>{video_metadata.resolution.join(' × ')}</strong>
            </div>
            <div className="metadata-item">
              <span>FPS:</span>
              <strong>{video_metadata.fps}</strong>
            </div>
            <div className="metadata-item">
              <span>Всего кадров:</span>
              <strong>{video_metadata.total_frames}</strong>
            </div>
          </div>
        </div>

        {/* Обобщенные характеристики */}
        <div className="analytics-section">
          <h3>Обобщенные характеристики</h3>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">Резких движений</div>
              <div className="metric-value">{aggregated_features.total_abrupt_movements}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Движений в минуту</div>
              <div className="metric-value">{aggregated_features.movements_per_minute.toFixed(1)}</div>
            </div>
          </div>

          {/* Метрики симметрии */}
          <div className="subsection">
            <h4>Симметрия движений</h4>
            <div className="symmetry-grid">
              {Object.entries(aggregated_features.symmetry_metrics).map(([key, value]) => (
                <div key={key} className="symmetry-item">
                  <div className="symmetry-label">{translateKey(key)}</div>
                  <div className="symmetry-value">
                    <div className={`symmetry-score ${value > 0.7 ? 'good' : value > 0.5 ? 'medium' : 'poor'}`}>
                      {(value * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

          {/* Предварительная оценка */}
          {mlData && mlData.available === false && (
             <div className="analytics-section">
          <h3>Оценка риска</h3>
          <div className={`risk-assessment ${getRiskColor(preliminary_annotation.risk_score)}`}>
            <div className="risk-score">
              <div className="score-label">Оценка риска</div>
              <div className="score-value">{preliminary_annotation.risk_score}/5</div>
            </div>
            <div className="risk-factors">
              <div className="factors-label">Факторы риска:</div>
              <div className="factors-list">
                {preliminary_annotation.risk_factors.map(factor => (
                  <span key={factor} className="factor-tag">
                    {translateKey(factor)}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        )}
       

        {/* Качество анализа */}
        <div className="analytics-section">
          <h3>Качество определение позы</h3>
          <div className="quality-metrics">
            <div className="quality-item">
              <span>Обнаружение:</span>
              <span className="quality-value">
                {(quality_metrics.detection_rate * 100 <= 100 ? quality_metrics.detection_rate * 100 : 100).toFixed(1)}%
              </span>
            </div>
            <div className="quality-item">
              <span>Уверенность:</span>
              <span className="quality-value">
                {(quality_metrics.avg_keypoint_confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="quality-item">
              <span>Пропущено кадров:</span>
              <span className="quality-value">
                {quality_metrics.missing_frames < 0 ? 0: quality_metrics.missing_frames}
              </span>
            </div>
          </div>
        </div>

        {/* Подробные метрики по суставам */}
        <div className="analytics-section">
          <h3>Детальные метрики по суставам</h3>
          <div className="joints-tabs">
            {Object.entries(aggregated_features.amplitude_features).map(([joint, data]) => (
              <div key={joint} className="joint-card">
                <h4>{translateKey(joint)}</h4>
                <div className="joint-metrics">
                  <div className="joint-metric">
                    <span>Средняя скорость:</span>
                    <span>{data.mean_speed.toFixed(1)}</span>
                  </div>
                  <div className="joint-metric">
                    <span>Максимальная скорость:</span>
                    <span>{data.max_speed.toFixed(1)}</span>
                  </div>
                  <div className="joint-metric">
                    <span>Доминирующая частота:</span>
                    <span>
                      {aggregated_features.frequency_features[joint]?.dominant_frequency_hz?.toFixed(2) || '—'} Гц
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Итоговая рекомендация внизу */}
      {(mlData || preliminary_annotation) && (
        <div className="final-recommendation-bar">
          <div className="recommendation-content">
            <strong className='recommendation-text'>Итоговая рекомендация:</strong>
            <span className="recommendation-text">
              {getFinalRecommendation(preliminary_annotation, mlData)}
            </span>
          </div>
    
        </div>
      )}
    </div>
  </div>
);
};

export { VideoAnalyticsModal };