import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import './authorization.css';
import Input from '../../utils/input/Input';
import { registration, auth } from '../../actions/user';

const Registration = () => {
  const dispatch = useDispatch();
  const loader = useSelector((state) => state.app.loader);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isChecked, setIsChecked] = useState(false);
  const [date, setDate] = useState('');
  const [error, setError] = useState('Пожалуйста, выберите дату рождения.');
  const [gender, setGender] = useState('male');

  const handleDateChange = (event) => {
    const selectedDate = event.target.value;
    setDate(selectedDate);

    // Валидация даты
    const today = new Date();
    const inputDate = new Date(selectedDate);

    // Проверяем, что дата не в будущем
    if (inputDate > today) {
      setError('Дата рождения не может быть в будущем.');
    } else if (!selectedDate) {
      setError('Пожалуйста, выберите дату рождения.');
    } else {
      setError(''); // Сбросить ошибку, если дата валидна
    }
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

  return (
    <div className="authorization">
      <div className="authorization__header">Регистрация</div>
      {/* Email */}
      <Input value={email} setValue={setEmail} type="text" placeholder="Введите email..." />
      {/* Password */}
      <Input value={password} setValue={setPassword} type="password" placeholder="Введите пароль..." />
      {/* Дата рождения */}
      <div className="authorization__field-date">
        <label
          style={{
            fontSize: '17px',
            whiteSpace: 'nowrap',
            textAlign: 'left',
          }}
          htmlFor="date"
        >
          Дата рождения:
          <br />
        </label>
        <input className="custom-date-input" style={{ cursor: 'pointer' }} type="date" id="date" value={date} onChange={handleDateChange} />
        {error && <p className="authorization__field-error">{error}</p>}
      </div>
      {/* ПОЛ */}
      <div className="authorization__field-gender">
        <label style={{ whiteSpace: 'nowrap', fontSize: '17px', marginRight: '10px' }} htmlFor="gender">
          Пол:
        </label>
        <select id="gender" value={gender} onChange={(event) => setGender(event.target.value)}>
          <option value="male">Мужской</option>
          <option value="female">Женский</option>
        </select>
      </div>

      {/* Чекбокс */}
      <label className="authorization__field " style={{ display: 'flex' }}>
        <label className="custom-checkbox">
          <input type="checkbox" checked={isChecked} onChange={() => setIsChecked(!isChecked)} style={{}}></input>
          <span></span>
        </label>
        <span style={{ whiteSpace: 'nowrap', fontSize: '12px', marginLeft: '20px' }}>
          Соглашаюсь с {''}
          <a href="/privacy.html" style={{ color: '#56C3E9', textDecoration: 'none' }}>
            договором
          </a>
          {''} на обработку персональных данных
        </span>
        {!isChecked && <p className="authorization__field-error">Пожалуйста, подтвердите, что вы согласны с условиями.</p>}
      </label>
      <button
        style={{ opacity: !isChecked ? 0.5 : 1 }}
        className="authorization__btn"
        onClick={() => dispatch(registration(email, password, date, gender))}
        disabled={!isChecked}
      >
        Зарегистрироваться
      </button>
    </div>
  );
};

export default Registration;
