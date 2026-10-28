import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VideoPlayer from './VideoPlayer';
import { $api  } from '../../../http';

const VideoList = ({ token }) => {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await $api.get('/api/files/videos', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVideos(response.data);
    } catch (error) {
      console.error('Error fetching videos:', error);
    }
  };

  return (
    <div className="video-library">
      <div className="video-list">
        {videos.map(video => (
          <div key={video._id} className="video-item" onClick={() => setSelectedVideo(video._id)}>
            <div className="video-thumbnail">
              <img src={`/api/video/thumbnail/${video._id}`} alt={video.name} />
            </div>
            <div className="video-title">{video.name}</div>
          </div>
        ))}
      </div>
      
      {selectedVideo && (
        <div className="video-player-container">
          <VideoPlayer fileId={selectedVideo} token={token} />
        </div>
      )}
    </div>
  );
};

export default VideoList;