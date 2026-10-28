import React, { useEffect, useState } from "react";
import Input from "../../utils/input/Input";
import { useDispatch, useSelector } from "react-redux";
import { setPopupDisplay } from "../../reducers/fileReducer";
import { changeLink } from "../../actions/file";
import { hideChange } from "../../reducers/linksReducer";

const PopupLinkChange = () => {
  let [link, setLink] = useState("");
  let [linkName, setLinkName] = useState("");
  const popupDisplay = useSelector((state) => state.files.popupDisplay);
  const fileId = useSelector((state) => state.links.id);
  const currentLinkName = useSelector((state) => state.links.currentLinkName);
  const currentLink = useSelector((state) => state.links.currentLink);
  const linkNameOld = currentLinkName;
  const linkOld = currentLink;
  const dispatch = useDispatch();

  useEffect(() => {
    if (popupDisplay === "none") {
    }
  }, [popupDisplay]);

  useEffect(() => {
    setLink(currentLink);
  }, [currentLink]);

  useEffect(() => {
    setLinkName(currentLinkName);
  }, [currentLinkName]);

  function changeHandler() {
    if (linkNameOld === linkName && linkOld === link) {
      dispatch(setPopupDisplay("none"));
      dispatch(hideChange());
    } else {
      dispatch(changeLink(linkNameOld, linkName, link, fileId));
      dispatch(setPopupDisplay("none"));
      dispatch(hideChange());
    }
  }

  function closePopup() {
    dispatch(setPopupDisplay("none"));
    dispatch(hideChange());
  }

  return (
    <div
      className="popup"
      onClick={() => closePopup()}
      style={{ display: popupDisplay }}
    >
      <div
        className="popup__content"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="popup__header">
          <div className="popup__title">изменить ссылку</div>
          <button className="popup__close" onClick={() => closePopup()}>
            X
          </button>
        </div>
        <Input
          type="text"
          placeholder="Введите название ссылки..."
          value={linkName}
          setValue={setLinkName}
        />
        <Input
          type="text"
          placeholder="Введите ссылку..."
          value={link}
          setValue={setLink}
        />
        <button className="popup__create" onClick={() => changeHandler()}>
          Изменить
        </button>
      </div>
    </div>
  );
};

export default PopupLinkChange;
