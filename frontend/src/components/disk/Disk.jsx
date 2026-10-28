import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { getFiles, getLinks, uploadFile } from '../../actions/file';
import FileList from './fileList/FileList';
import './disk.css';
import Popup from './Popup';
import {
  setCurrentDir,
  //   setFileView,
  setPopupDisplay,
} from '../../reducers/fileReducer';
import Uploader from './uploader/Uploader';
import LinkList from './linkList/LinkList';
import { hideLinks } from '../../reducers/linksReducer';
import PopupLink from './PopupLink';
import PopupLinkChange from './PopupLinkChange';
import ProgressBar from './progressBar';
import { totalSpace } from '../../utils/sizeFormat';
import { auth } from '../../actions/user';
import { TextForm } from './textForm/TextForm';
import { TagsModal } from './TagsModal';

const Disk = () => {
  const dispatch = useDispatch();
  const currentDir = useSelector((state) => state.files.currentDir);
  const loader = useSelector((state) => state.app.loader);
  const dirStack = useSelector((state) => state.files.dirStack);
  const [dragEnter, setDragEnter] = useState(false);
  const [sort, setSort] = useState('type');
  const [isTextForm, setIsTextForm] = useState(false);
  const isLinks = useSelector((state) => state.links.isLinks);
  const links = useSelector((state) => state.links.links);
  const isChange = useSelector((state) => state.links.isChange);
  const usedSpace = useSelector((state) => state.user.currentUser.usedSpace);

  const [files, setFiles] = useState(null);
  const [writeFile, setWriteFile] = useState(null);
  const [openTagsModal, setOpenTagsModal] = useState(false);

  let isExistFreeSpace = null;
  const occupiedSpacePercent = (usedSpace / totalSpace) * 100;
  if (occupiedSpacePercent >= 100) {
    isExistFreeSpace = false;
  } else {
    isExistFreeSpace = true;
  }

  useEffect(() => {
    dispatch(auth());
    dispatch(getFiles(currentDir, sort));
    if (isLinks) {
      dispatch(getLinks(links));
    }
  }, [currentDir, sort, usedSpace]);

  function showPopupHandler() {
    dispatch(setPopupDisplay('flex'));
  }

  function showPopupHandlerLinks() {
    dispatch(setPopupDisplay('flex'));
  }

  function backClickHandler() {
    if (currentDir !== null) {
      const backDirId = dirStack.pop();
      dispatch(setCurrentDir(backDirId));
    }
  }

  function backLinksClickHandler() {
    dispatch(hideLinks());
  }

  function fileUploadHandler(files, tags) {
    try {
      console.log(files);
      let currentUsedSpace = usedSpace;
      dispatch(auth());
      files.forEach((file) => {
        currentUsedSpace += file.size;
        if (currentUsedSpace >= totalSpace) {
          setFiles(null);
          throw new Error('Не хватает памяти !');
        }
        dispatch(uploadFile(file, currentDir, tags));
      });
      setFiles(null);
      dispatch(getFiles(currentDir, sort));
      dispatch(auth());
    } catch (e) {
      console.log('fileUploadHandler', e);
      alert('Не хватает памяти !');
    }
  }

  function createAndUploadTextFileHandler(name, content, tags) {
    try {
      let currentUsedSpace = usedSpace;
      setIsTextForm(false);
      dispatch(auth());
      const blob = new Blob([content], { type: 'text/plain' });
      const file = new File([blob], `${name}.txt`, { type: 'text/plain' });
      currentUsedSpace += file.size;
      if (currentUsedSpace >= totalSpace) {
        setWriteFile(null);
        throw new Error('Не хватает памяти !');
      }
      dispatch(uploadFile(file, currentDir, tags));
      setWriteFile(null);
      dispatch(getFiles(currentDir, sort));
      dispatch(auth());
    } catch (e) {
      console.log('createAndUploadTextFileHandler', e);
      alert('Не хватает места!!!');
    }
  }

  function dragEnterHandler(event) {
    dispatch(auth());
    event.preventDefault();
    event.stopPropagation();
    setDragEnter(true);
  }

  function dragLeaveHandler(event) {
    dispatch(auth());
    event.preventDefault();
    event.stopPropagation();
    setDragEnter(false);
  }

  function dropHandler(event) {
    dispatch(auth());
    event.preventDefault();
    event.stopPropagation();
    let files = [...event.dataTransfer.files];
    files.forEach((file) => dispatch(uploadFile(file, currentDir)));
    setDragEnter(false);
  }

  const handleFileSelect = (event) => {
    const selectedFiles = [...event.target.files];
    if (selectedFiles) {
      setFiles(selectedFiles);
      setOpenTagsModal(true);
    }
  };

  const handleWriteFileSelect = (name, content) => {
    if (name && content) {
      setWriteFile({ name, content });
      setOpenTagsModal(true);
    }
  };

  const handleSaveTags = (selectedTags) => {
    if (files && !writeFile) {
      fileUploadHandler(files, selectedTags);
    } else if (!files && writeFile) {
      createAndUploadTextFileHandler(writeFile.name, writeFile.content, selectedTags);
    }
    setOpenTagsModal(false);
    console.log('Выбранные теги:', selectedTags);
  };

  const handleRefresh = () => {
    dispatch(auth());
    dispatch(getFiles(currentDir, sort));
  };

  if (loader) {
    return (
      <div className="loader">
        <div className="lds-roller">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
      </div>
    );
  }

  return isLinks ? (
    <div className="disk">
      <div className="disk__btns">
        {/* <svg
          onClick={() => backLinksClickHandler()}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          width="32"
          height="32"
          className="back-icon"
        >
          <path
            id="first"
            d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zm-1 13l-4-4 4-4v3h7v2h-7v3z"
          />
          <path id="second" d="M0 0h24v24H0z" fill="none" />
        </svg> */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          onClick={() => showPopupHandlerLinks()}
          viewBox="0 0 24 24"
          width="32"
          height="32"
          className="create-link-icon"
        >
          <path d="M12.11,15.39,8.23,19.27a2.47,2.47,0,0,1-3.5,0,2.46,2.46,0,0,1,0-3.5l3.88-3.88a1,1,0,1,0-1.42-1.42L3.31,14.36a4.48,4.48,0,0,0,6.33,6.33l3.89-3.88a1,1,0,0,0-1.42-1.42Zm-3.28-.22a1,1,0,0,0,.71.29,1,1,0,0,0,.71-.29l4.92-4.92a1,1,0,1,0-1.42-1.42L8.83,13.75A1,1,0,0,0,8.83,15.17ZM21,18H20V17a1,1,0,0,0-2,0v1H17a1,1,0,0,0,0,2h1v1a1,1,0,0,0,2,0V20h1a1,1,0,0,0,0-2Zm-4.19-4.47,3.88-3.89a4.48,4.48,0,0,0-6.33-6.33L10.47,7.19a1,1,0,1,0,1.42,1.42l3.88-3.88a2.47,2.47,0,0,1,3.5,0,2.46,2.46,0,0,1,0,3.5l-3.88,3.88a1,1,0,0,0,0,1.42,1,1,0,0,0,1.42,0Z" />
        </svg>
      </div>
      <LinkList />
      {isChange ? <PopupLinkChange /> : <PopupLink />}
    </div>
  ) : !dragEnter ? (
    <div className="disk" onDragEnter={dragEnterHandler} onDragLeave={dragLeaveHandler} onDragOver={dragEnterHandler}>
      <div className="disk__btns">
        {/* <svg
          onClick={() => backClickHandler()}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          width="32"
          height="32"
          className="back-icon"
        >
          <path id="first" d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zm-1 13l-4-4 4-4v3h7v2h-7v3z" />
          <path id="second" d="M0 0h24v24H0z" fill="none" />
        </svg> */}

        {/* <svg
          xmlns="http://www.w3.org/2000/svg"
          onClick={() => showPopupHandler()}
          viewBox="0 0 24 24"
          width="32"
          height="32"
          className="create-dir-icon"
        >
          <path
            id="primary"
            d="M7,18H4a1,1,0,0,1-1-1V4A1,1,0,0,1,4,3H9a1,1,0,0,1,.71.29l2.41,2.42a1,1,0,0,0,.71.29H20a1,1,0,0,1,1,1V9"
          />
          <path id="second" d="M16,21V13m-4,4h8" />
        </svg> */}
        {isExistFreeSpace && (
          <>
            <div className="disk__upload">
              <label htmlFor="disk__upload-input" className="disk__upload-label">
                Загрузить файл
              </label>
              <input multiple={true} onChange={handleFileSelect} type="file" id="disk__upload-input" className="disk__upload-input" />
            </div>
            <div className="disk__write-text">
              <button className="disk__write-text-label" onClick={() => setIsTextForm(true)}>
                Написать текст
              </button>
              {isTextForm && <TextForm onClose={() => setIsTextForm(false)} onCreate={(name, content) => handleWriteFileSelect(name, content)} />}
            </div>
            <TagsModal open={openTagsModal} onClose={() => setOpenTagsModal(false)} onSave={handleSaveTags} />
          </>
        )}
          <ProgressBar totalSpace={totalSpace} usedSpace={usedSpace} />
          
           <button className="disk__refresh-btn" onClick={handleRefresh} title="Обновить список файлов">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            <path d="M0 0h24v24H0z" fill="none"/>
          </svg>
        </button>

        <select value={sort} onChange={(e) => setSort(e.target.value)} className="disk__select">
          <option className="disk__option" value="name">
            По имени
          </option>
          <option className="disk__option" value="type">
            По типу
          </option>
          <option className="disk__option" value="date">
            По дате
          </option>
        </select>
      </div>
      <FileList />
      <Popup />
      <Uploader />
    </div>
  ) : (
    <div className="drop-area" onDrop={dropHandler} onDragEnter={dragEnterHandler} onDragLeave={dragLeaveHandler} onDragOver={dragEnterHandler}>
      Перетащите файлы сюда
    </div>
  );
};

export default Disk;
