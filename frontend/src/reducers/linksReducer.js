const SHOW_LINKS = 'SHOW_LINKS'
const HIDE_LINKS = 'HIDE_LINKS'
const SHOW_CHANGE = "SHOW_CHANGE"
const HIDE_CHANGE = "HIDE_CHANGE"
const SET_LINKS = "SET_LINKS"
const ADD_LINK = "ADD_LINK"
const DELETE_LINK = "DELETE_LINK"
const SET_ID = "SET_ID"
const CHANGE_LINK_NAME = "CHANGE_LINK_NAME"
const CHANGE_LINK = "CHANGE_LINK"




const defaultState = {
    isLinks: false,
    isChange: false,
    links: [],
    id: '',
    currentLinkName: '',
    currentLink: ''
}

export default function linksReducer(state = defaultState, action) {
    switch (action.type) {
        case SHOW_LINKS: return { ...state, isLinks: true }
        case HIDE_LINKS: return { ...state, isLinks: false }
        case SHOW_CHANGE: return { ...state, isChange: true }
        case HIDE_CHANGE: return { ...state, isChange: false }
        case ADD_LINK: return { ...state, links: [...state.links, action.payload] }
        case SET_LINKS: return { ...state, links: action.payload }
        case DELETE_LINK: return { ...state, links: [...state.links.filter(link => link.name !== action.payload)] }
        case SET_ID: return { ...state, id: action.payload }
        case CHANGE_LINK_NAME: return { ...state, currentLinkName: action.payload }
        case CHANGE_LINK: return { ...state, currentLink: action.payload }
        default:
            return state
    }
}


export const showLinks = () => ({ type: SHOW_LINKS })
export const hideLinks = () => ({ type: HIDE_LINKS })
export const showChange = () => ({ type: SHOW_CHANGE })
export const hideChange = () => ({ type: HIDE_CHANGE })
export const setLinks = (links) => ({ type: SET_LINKS, payload: links })
export const addLinkAction = (link) => ({ type: ADD_LINK, payload: link })
export const deleteLink = (name) => ({ type: DELETE_LINK, payload: name })
export const setId = (id) => ({ type: SET_ID, payload: id })
export const changeLinkName = (name) => ({ type: CHANGE_LINK_NAME, payload: name })
export const changeLink = (link) => ({ type: CHANGE_LINK, payload: link })