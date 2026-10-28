import React from 'react';
import size, { getColorOfSpace } from '../../utils/sizeFormat';

const ProgressBar = ({ totalSpace, usedSpace }) => {
  const occupiedSpacePercent = (usedSpace / totalSpace) * 100;
  const colorOfSpace = getColorOfSpace(usedSpace, totalSpace);

  return (
    <div style={styles.wrapper}>
      <div style={styles.container}>
        <div style={{ ...styles.progressBar, backgroundColor: colorOfSpace, width: `${occupiedSpacePercent}%` }} />
      </div>
      <div style={styles.labels}>
        <span>
          {size(usedSpace)} из {size(totalSpace)}
        </span>
      </div>
    </div>
  );
};

const styles = {
  wrapper: {
    position: 'relative',
    top: '0px',
    marginLeft: 'auto',
    width: '20%',
  },
  container: {
    top: '10px',
    position: 'absolute',
    width: '100%',
    height: '10px',
    backgroundColor: '#e0e0e0',
    borderRadius: '8px',
    padding: '5px',
    boxShadow: 'inset 0 0 5px rgba(255, 255, 255, 0.98)',
  },
  progressBar: {
    position: 'absolute',
    top: '0px',
    left: '0px',
    height: '10px',
    borderRadius: '5px',
    transition: 'width 0.3s ease',
  },
  labels: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: '#555',
    marginTop: '25px', // Добавлен отступ для размещения текста под полосой
  },
};

export default ProgressBar;
