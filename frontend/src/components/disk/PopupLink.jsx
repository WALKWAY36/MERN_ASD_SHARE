import React, { useEffect, useState } from 'react';
import Input from '../../utils/input/Input';
import { useDispatch, useSelector } from 'react-redux';
import { setPopupDisplay } from '../../reducers/fileReducer';
import { addLink } from '../../actions/file';
import { auth } from '../../actions/user';

const PopupLink = () => {
  const [link, setLink] = useState('');
  const [linkName, setLinkName] = useState('');
  const popupDisplay = useSelector((state) => state.files.popupDisplay);
  const fileId = useSelector((state) => state.links.id);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(auth());
    if (popupDisplay === 'none') {
      setLinkName('');
      setLink('');
    }
  }, [popupDisplay]);

  function addHandler() {
    dispatch(addLink(linkName, link, fileId));
    dispatch(setPopupDisplay('none'));
  }

  return (
    <div className="popup" onClick={() => dispatch(setPopupDisplay('none'))} style={{ display: popupDisplay }}>
      <div className="popup__content" onClick={(event) => event.stopPropagation()}>
        <div className="popup__header">
          <div className="popup__title">Добавить новую ссылку</div>
          <button className="popup__close" onClick={() => dispatch(setPopupDisplay('none'))}>
            X
          </button>
        </div>
        <Input type="text" placeholder="Введите название ссылки..." value={linkName} setValue={setLinkName} />
        <Input type="text" placeholder="Введите ссылку..." value={link} setValue={setLink} />
        <button className="popup__create" onClick={() => addHandler()}>
          Добавить
        </button>
      </div>
    </div>
  );
};

export default PopupLink;
