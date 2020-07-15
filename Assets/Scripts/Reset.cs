using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class Reset : MonoBehaviour
{
    public void ButtonReset()
    {
        Resetter.Reset();
    }
}

public static class Resetter
{
    public static void Reset()
    {
        Debug.Log("Resetter.Reset() called");
        Buttons.up_button = false;
        Buttons.right_button = false;
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }
}
