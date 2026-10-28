import React from "react";
import { useDispatch, useSelector } from "react-redux";
import linkLogo from "../../../../assets/img/link.png";
import "./link.css";
import { deleteFileLink } from "../../../../actions/file";
import { setPopupDisplay } from "../../../../reducers/fileReducer";
import {
  changeLink,
  changeLinkName,
  showChange,
} from "../../../../reducers/linksReducer";

const Link = ({ link }) => {
  const dispatch = useDispatch();
  const fileId = useSelector((state) => state.links.id);

  function deleteClickHandler(e) {
    e.stopPropagation();
    dispatch(deleteFileLink(link, fileId));
  }

  function changeClickHandler(e) {
    e.stopPropagation();
    dispatch(changeLinkName(link.name));
    dispatch(changeLink(link.content));
    dispatch(showChange());
    dispatch(setPopupDisplay("flex"));
  }

  return (
    <div>
      <div className="link">
        <img src={linkLogo} alt="" height={35} className="link__img" />
        <div className="link__name">{link.name}</div>
        <div className="link__linke">{link.content}</div>
        <button
          onClick={(e) => changeClickHandler(e)}
          className="link__btn link__change"
        >
          изменить
        </button>
        <button
          onClick={(e) => deleteClickHandler(e)}
          className="link__btn link__delete"
        >
          Удалить
        </button>
      </div>
    </div>
  );
};

export default Link;
