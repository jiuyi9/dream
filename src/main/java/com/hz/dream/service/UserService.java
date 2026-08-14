package com.hz.dream.service;

import com.hz.dream.dao.UserMapper;
import com.hz.dream.po.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserMapper userMapper;

    public List<User> list() {
        return userMapper.findAll();
    }

    public User get(Long id) {
        return userMapper.findById(id);
    }

    public User create(User user) {
        userMapper.insert(user);
        return user;
    }

    public User update(User user) {
        userMapper.update(user);
        return user;
    }

    public void delete(Long id) {
        userMapper.deleteById(id);
    }
}