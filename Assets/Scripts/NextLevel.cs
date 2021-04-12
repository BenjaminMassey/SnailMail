using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class NextLevel : MonoBehaviour
{
    public void Perform()
    {
        //yield return new WaitForSeconds(delay);
        LevelEnd.level_completed = false;
        string levelStr = SceneManager.GetActiveScene().name;
        levelStr = levelStr.Replace("Level", "");
        int levelNum = int.Parse(levelStr);
        string levelName = "Level" + (levelNum + 1).ToString();
        if (levelNum < Unlocks.num_levels)
        {
            SceneManager.LoadScene(levelName);
        }
        else
        {
            SceneManager.LoadScene("End");
        }
    }
}
