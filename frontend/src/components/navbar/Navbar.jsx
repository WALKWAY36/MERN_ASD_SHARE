import React from 'react';
import './navbar.css';
import Logo from '../../assets/img/logo.svg';
import { NavLink } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
// import { logout } from '../../reducers/userReducer';
import { logoutService } from '../../actions/user';
// import { getFiles, searchFiles } from "../../actions/file";
// import { showLoader } from "../../reducers/appReducer";
import avatarLogo from '../../../src/assets/img/avatar.svg';
import { API_URL } from '../../config';

const Navbar = () => {
  const isAuth = useSelector((state) => state.user.isAuth);
  // const currentDir = useSelector((state) => state.files.currentDir);
  const currentUser = useSelector((state) => state.user.currentUser);
  const dispatch = useDispatch();
  // const [searchName, setSearchName] = useState("");
  // const [searchTimeout, setSearchTimeout] = useState(false);
  const avatar = currentUser.avatar ? `${API_URL + currentUser.avatar}` : avatarLogo;
  // function searchChangeHandler(e) {
  //   setSearchName(e.target.value);
  //   if (searchTimeout !== false) {
  //     clearTimeout(searchTimeout);
  //   }
  //   dispatch(showLoader());
  //   if (e.target.value !== null) {
  //     setSearchTimeout(
  //       setTimeout(
  //         (value) => {
  //           dispatch(searchFiles(value));
  //         },
  //         500,
  //         e.target.value
  //       )
  //     );
  //   } else {
  //     dispatch(getFiles(currentDir));
  //   }
  // }

  return (
    <div className="navbar">
      <div className="container">
        <img src={Logo} alt="" className="navbar__logo" />
        <div className="navbar__header">
          <NavLink to="/autmama/">Аутмама облако</NavLink>
        </div>
        {/* {isAuth && (
          <input
            value={searchName}
            onChange={(e) => searchChangeHandler(e)}
            className="navbar__search"
            type="text"
            placeholder="Название файла..."
          />
        )} */}
        {!isAuth && (
          <div className="navbar__login">
            <NavLink to="/autmama/login/">Войти</NavLink>
          </div>
        )}
        {/* {!isAuth && (
          <div className="navbar__registration">
            <NavLink to="/autmama/registration">Регистрация</NavLink>
          </div>
        )} */}
        {isAuth && (
          <div className="navbar__login" onClick={() => dispatch(logoutService())}>
            Выход
          </div>
        )}
        {isAuth && (
          <NavLink to="/autmama/profile">
            <img className="navbar__avatar" src={avatar} alt="avatar" />
          </NavLink>
        )}
      </div>
    </div>
  );
};
export default Navbar;
