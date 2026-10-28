import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Chip } from '@mui/material';
import Autocomplete from '@mui/material/Autocomplete';

const tagsList = ['Удары', 'Вскрики'];

const TagsModal = ({ open, onClose, onSave }) => {
  const [selectedTags, setSelectedTags] = useState([]);

  const handleSave = () => {
    onSave(selectedTags);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>Выберите теги</DialogTitle>
      <DialogContent>
        <Autocomplete
          multiple
          options={tagsList}
          value={selectedTags}
          onChange={(_, value) => setSelectedTags(value)}
          renderTags={(value, getTagProps) => value.map((option, index) => <Chip key={option} label={option} {...getTagProps({ index })} />)}
          renderInput={(params) => <TextField {...params} label="Теги" />}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отменить</Button>
        <Button onClick={handleSave} variant="contained">
          Сохранить
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export { TagsModal };
