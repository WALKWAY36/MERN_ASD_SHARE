import { useState } from 'react';
import './textForm.css';

const TextForm = ({ onClose, onCreate }) => {
  const [name, setName] = useState(null);
  const [content, setContent] = useState(null);

  return (
    <div className="text-form">
      <div className="text-form__background"></div>
      <div className="text-form__form">
        <button className="text-form__button-close" onClick={onClose}>
          X
        </button>
        <div className="text-form__container">
          <h3 className="text-form-header">Создание текста</h3>
          <div className="text-form__name">
            <label className="text-form__name-label">Название документа</label>
            <input className="text-form__name-input" onChange={(e) => setName(e.target.value)}></input>
          </div>
          <div className="text-form__content">
            <label className="text-form__content-label">Введите текст</label>
            <textarea className="text-form__content-input" cols="40" rows="5" onChange={(e) => setContent(e.target.value)}></textarea>
          </div>
        </div>
        <button className="text-form__button-create" onClick={() => onCreate(name, content)}>
          Создать
        </button>
      </div>
    </div>
  );
};

export { TextForm };
