﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class LevelSelectButton : MonoBehaviour
{
    public void onPress()
    {
        // Name will be "LevelX Button". Want to load "LevelX"
        string[] parts = name.Split(' ');
        LevelEnd.level_completed = false;
        SceneManager.LoadScene(parts[0]);
    }
}
