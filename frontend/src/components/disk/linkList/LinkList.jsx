import { useSelector } from "react-redux";
import "./linkList.css";
import React from "react";
import Link from "./link/Link";
import { CSSTransition, TransitionGroup } from "react-transition-group";

const LinkList = () => {
  const links = useSelector((state) => state.links.links);

  if (links.length === 0) {
    return <div className="loader">Ссылки не найдены</div>;
  }
  return (
    <div className="linklist">
      <div className="linklist__header">
        <div className="linklist__name">Название</div>
        <div className="linklist__link">Ссылка</div>
      </div>
      <TransitionGroup>
        {links.map((link) => (
          <CSSTransition
            key={link.name}
            timeout={500}
            classNames={"link"}
            exit={false}
          >
            <Link link={link} />
          </CSSTransition>
        ))}
      </TransitionGroup>
    </div>
  );
};

export default LinkList;
